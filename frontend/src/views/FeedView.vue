<template>
  <div class="feed">
    <div class="filter-bar">
      <div class="filter-group">
        <div class="risk-card-group">
          <div 
            class="risk-select-card all" 
            :class="{ active: !filters.riskLevel }" 
            @click="setRisk('')"
          >全部</div>
          <div 
            class="risk-select-card low" 
            :class="{ active: filters.riskLevel === 'low' }" 
            @click="setRisk('low')"
          >低风险 {{ formatRiskCount('low') }}</div>
          <div 
            class="risk-select-card medium" 
            :class="{ active: filters.riskLevel === 'medium' }" 
            @click="setRisk('medium')"
          >中风险 {{ formatRiskCount('medium') }}</div>
          <div 
            class="risk-select-card high" 
            :class="{ active: filters.riskLevel === 'high' }" 
            @click="setRisk('high')"
          >高风险 {{ formatRiskCount('high') }}</div>
          <div 
            class="risk-select-card critical" 
            :class="{ active: filters.riskLevel === 'critical' }" 
            @click="setRisk('critical')"
          >极高风险 {{ formatRiskCount('critical') }}</div>
        </div>
      </div>
    </div>

    <div class="posts-container">
      <div v-if="isLoading && posts.length === 0" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="posts.length === 0" class="empty-state">
        <el-empty description="暂无帖子数据">
          <button type="button" class="refresh-btn-native" @click="refreshPosts">
            刷新数据
          </button>
        </el-empty>
      </div>
      
      <template v-else>
        <div class="posts-list">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-card"
            :class="post.risk_level"
          >
            <!-- Agent 标签移至左上角 -->
            <div class="author-card">
              <span class="author-label">Agent</span>
              <span class="author-name-cn">{{ getAgentName(post) }}</span>
            </div>

            <div class="post-header">
              <a 
                v-if="post.title || post.url" 
                class="post-title-link" 
                :href="post.url || '#'" 
                target="_blank"
              >
                {{ post.title || '查看原帖' }}
              </a>
              <div class="risk-badge" :style="{ '--badge-color': getRiskColor(post.risk_level) }">
                {{ getRiskLabel(post.risk_level) }}
              </div>
            </div>
            
            <div class="post-content">
              <p>{{ post.content }}</p>
            </div>
            
            <div v-if="post.translation" class="post-translation">
              <div class="translation-header">
                <el-icon size="14"><Edit /></el-icon>
                <span>翻译结果</span>
              </div>
              <p>{{ post.translation }}</p>
            </div>
            
            <div class="post-footer">
              <!-- 时间移至左下角 -->
              <span class="post-time-footer">{{ formatTime(post.created_at) }}</span>
              <button 
                type="button" 
                class="translate-btn" 
                @click="translatePost(post)"
                :disabled="isTranslating(post.id)"
              >
                <span>{{ isTranslating(post.id) ? '翻译中...' : '翻译' }}</span>
              </button>
            </div>
          </div>
        </div>
        
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="feedTotal"
            :page-sizes="[10, 20, 30, 50]"
            layout="total, sizes, jumper, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </template>
    </div>
    
    <el-dialog
      v-model="detailDialogVisible"
      title="帖子详情"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedPost" class="post-detail">
        <div class="detail-header">
          <el-avatar :size="48" class="author-avatar">
            {{ selectedPost.author_id?.charAt(0) || '?' }}
          </el-avatar>
          <div class="author-meta">
            <span class="author-name">{{ getAgentName(selectedPost) }}</span>
            <span class="post-time">{{ formatTime(selectedPost.created_at) }}</span>
          </div>
        </div>
        
        <div class="detail-content">
          <h4>内容</h4>
          <p>{{ selectedPost.content }}</p>
          
          <div v-if="selectedPost.translation" class="translation-content">
            <h4>翻译结果</h4>
            <p>{{ selectedPost.translation }}</p>
          </div>
        </div>
        
        <div class="detail-stats">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="风险等级">
              <el-tag :type="getRiskType(selectedPost.risk_level)" effect="dark">
                {{ getRiskLabel(selectedPost.risk_level) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="阴谋指数">
              {{ (selectedPost.conspiracy_score || 0).toFixed(1) }}/10
            </el-descriptions-item>
            <el-descriptions-item label="情感">
              {{ selectedPost.sentiment !== undefined ? formatSentiment(selectedPost.sentiment) : '无数据' }}
            </el-descriptions-item>
            <el-descriptions-item label="社区">
              {{ selectedPost.submolt || 'general' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { 
  Document, 
  Refresh, 
  Edit,
  Loading,
  Warning
} from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import { translationApi, dashboardApi } from '@/api'
import { submoltLabels, riskLabels } from '@/locales'

const languageStore = useLanguageStore()
const store = useDataStore()
const { posts, feedTotal, isLoading, agents } = storeToRefs(store)

const riskDistribution = ref<Record<string, number>>({
  low: 0,
  medium: 0,
  high: 0,
  critical: 0
})

const filters = ref({
  riskLevel: '',
  submolt: ''
})

const currentPage = ref(1)
const pageSize = ref(30)
let refreshInterval: ReturnType<typeof setInterval> | null = null

const detailDialogVisible = ref(false)
const selectedPost = ref<any>(null)
const translatedPosts = ref<Map<string, string>>(new Map())
const translatingPosts = ref<Set<string>>(new Set())

/**
 * 获取风险分布数据
 */
const fetchRiskDistribution = async () => {
  try {
    const res = await dashboardApi.getRiskDistribution()
    riskDistribution.value = res.data || { low: 0, medium: 0, high: 0, critical: 0 }
  } catch (error) {
    console.error('Failed to fetch risk distribution:', error)
  }
}

/**
 * 格式化风险数量显示
 */
const formatRiskCount = (level: string) => {
  const count = riskDistribution.value[level] || 0
  if ((level === 'low' || level === 'medium') && count >= 1000) {
    return '(保留1000条)'
  }
  return `(${count})`
}

const getSubmoltLabel = (key: string) => {
  if (!key || !key.trim()) return '其他'
  const labels = submoltLabels[key]
  if (!labels) return '其他'
  return languageStore.locale === 'zh' ? labels.zh : labels.en
}

const getSubmoltColor = (key: string) => {
  if (!key || !key.trim()) return '#6b7280'
  return submoltLabels[key]?.color || '#6b7280'
}

const getRiskLabel = (level: string) => {
  if (!level || !level.trim()) return '未知'
  const labels = riskLabels[level]
  if (!labels) return level
  return languageStore.locale === 'zh' ? labels.zh : labels.en
}

const getRiskColor = (level: string) => {
  if (!level || !level.trim()) return '#6b7280'
  return riskLabels[level]?.color || '#6b7280'
}

const isTranslating = (postId: string) => {
  return translatingPosts.value.has(postId)
}

const getAgentName = (post: any) => {
  if (post.author_name && post.author_name.trim()) {
    return post.author_name
  }
  const authorId = post.author_id
  if (!authorId || authorId === 'unknown') return '匿名用户'
  if (agents.value.length > 0) {
    const agent = agents.value.find(a => a && a.id === authorId)
    if (agent && agent.name && agent.name.trim()) {
      return agent.name
    }
  }
  // 如果没有找到，从 UUID 中提取有意义的名称
  // UUID 格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  // 尝试提取最后一部分作为名称
  const parts = authorId.split('-')
  if (parts.length >= 5) {
    // 使用最后两部分生成名称
    const suffix = parts.slice(-2).join('')
    // 将十六进制转换为可见字符
    const name = decodeUUID(suffix)
    if (name) return name
  }
  return authorId.substring(0, 12)
}

const decodeUUID = (hex: string) => {
  // 简单解码：提取字母和数字
  const clean = hex.replace(/[^a-zA-Z0-9]/g, '')
  if (clean.length >= 8) {
    return clean.substring(0, 8)
  }
  return null
}

const getRiskType = (level: string) => {
  const types: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return types[level] || 'info'
}

const getSentimentType = (val: number) => {
  if (!val && val !== 0) return 'info'
  if (val > 0.3) return 'success'
  if (val < -0.3) return 'danger'
  return 'info'
}

const formatSentiment = (val: number) => {
  if (!val && val !== 0) return '中性'
  if (val > 0.3) return '积极'
  if (val < -0.3) return '消极'
  return '中性'
}

const formatTime = (timestamp: number) => {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

const setRisk = (level: string) => {
  filters.value.riskLevel = level
  currentPage.value = 1
  refreshPosts()
}

/**
 * 启动自动刷新
 */
const startAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  refreshInterval = setInterval(() => {
    refreshPosts()
  }, 30000)
}

const refreshPosts = async () => {
  await Promise.all([
    store.fetchFeed({
      page: currentPage.value,
      pageSize: pageSize.value,
      riskLevel: filters.value.riskLevel,
      submolt: filters.value.submolt
    }),
    fetchRiskDistribution()
  ])
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  refreshPosts()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  refreshPosts()
}

const viewPostDetail = (post: any) => {
  if (post.url) {
    window.open(post.url, '_blank')
  } else {
    selectedPost.value = post
    detailDialogVisible.value = true
  }
}

const translatePost = async (post: any) => {
  const cacheKey = post.id
  
  if (translatedPosts.value.has(cacheKey)) {
    post.translation = translatedPosts.value.get(cacheKey)
    return
  }
  
  if (translatingPosts.value.has(cacheKey)) {
    return
  }
  
  translatingPosts.value.add(cacheKey)
  
  try {
    const response = await translationApi.translate(post.content)
    if (response.data && response.data.translation) {
      translatedPosts.value.set(cacheKey, response.data.translation)
      post.translation = response.data.translation
    } else {
      post.translation = '[翻译失败]'
    }
  } catch (error: any) {
    console.error('Translation failed:', error)
    if (error?.code === 'ECONNABORTED' || String(error?.message || '').includes('timeout')) {
      post.translation = '[翻译超时]'
      return
    }
    const errorMsg = error.response?.data?.detail || '[翻译失败]'
    post.translation = errorMsg
  } finally {
    translatingPosts.value.delete(cacheKey)
  }
}

onMounted(() => {
  refreshPosts()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.feed {
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content {
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.title-icon {
  color: var(--accent-primary);
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.title-icon :deep(svg) {
  width: 28px;
  height: 28px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.refresh-btn .btn-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.refresh-btn-native {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border: none;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.refresh-btn-native:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.refresh-btn-native:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn-native .btn-icon {
  width: 16px;
  height: 16px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: rgba(30, 41, 59, 0.4);
  padding: 16px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 24px;
}

.risk-card-group {
  display: flex;
  gap: 8px;
}

.risk-select-card {
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
}

.risk-select-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.risk-select-card.active.all { background: rgba(148, 163, 184, 0.2); color: #f8fafc; border-color: #94a3b8; }
.risk-select-card.active.low { background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: #10b981; }
.risk-select-card.active.medium { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border-color: #f59e0b; }
.risk-select-card.active.high { background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: #ef4444; }
.risk-select-card.active.critical { background: rgba(220, 38, 38, 0.2); color: #fca5a5; border-color: #dc2626; }

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auto-refresh :deep(.el-switch__label) {
  color: var(--text-primary);
}

.posts-container {
  min-height: 400px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
}

.post-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
}

.post-card.low {
  border-left: 4px solid var(--accent-success);
}

.post-card.medium {
  border-left: 4px solid var(--accent-warning);
}

.post-card.high,
.post-card.critical {
  border-left: 4px solid var(--accent-danger);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.author-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  background: none;
  border: none;
  border-radius: 0;
  flex-shrink: 0;
  margin-bottom: 8px; /* 添加下边距，与下方标题保持间距 */
}

.author-label {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

.author-name-cn {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8; /* 修改为灰色 */
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}

.post-time-footer {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.8;
  white-space: nowrap;
}

.post-title-link {
  color: var(--text-primary);
  text-decoration: none;
  font-size: 1.2rem; /* 稍微放大 */
  font-weight: bold; /* 加粗 */
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all 0.2s ease;
  text-align: left; /* 靠左 */
  margin: 0; /* 移除外边距，紧靠左侧 */
}

.post-title-link:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}

.author-id {
  font-size: 11px;
  color: var(--text-muted);
  font-family: monospace;
  margin-top: 2px;
}

.post-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.post-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.post-title {
  font-size: 13px;
  color: var(--accent-primary);
  font-weight: 500;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.author-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.post-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.post-badges {
  display: flex;
  gap: 8px;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  border: 1px solid var(--badge-color, #6b7280);
  background: var(--badge-color, #6b7280);
  flex-shrink: 0;
  opacity: 0.9;
  margin-left: auto;
}

.submolt-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  border: 1px solid var(--badge-color, #6b7280);
  background: var(--badge-color, #6b7280);
  flex-shrink: 0;
  opacity: 0.7;
}

.submolt-badge:hover, .risk-badge:hover {
  opacity: 1;
}

.post-content {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.post-content p {
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
}

.post-time-header {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.8;
  white-space: nowrap;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.translate-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  background: none;
  color: #3b82f6;
  border: none;
  border-radius: 0;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: none;
  backdrop-filter: none;
}

.translate-btn:hover:not(:disabled) {
  background: none;
  color: #60a5fa;
  transform: none;
  box-shadow: none;
  text-decoration: underline;
}

.translate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: none;
  color: var(--text-muted);
}

.translate-btn .btn-icon {
  width: 14px;
  height: 14px;
}

.action-link {
  background: none;
  border: none;
  color: var(--accent-primary);
  font-size: 14px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.action-link:hover {
  background: var(--accent-primary);
  color: white;
}

.action-link .btn-icon {
  width: 14px;
  height: 14px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 20px;
  background: var(--bg-card);
  border-radius: 12px;
}

.post-detail {
  padding: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.detail-content {
  margin-bottom: 20px;
}

.detail-content h4 {
  margin: 0 0 8px 0;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
}

.detail-content p {
  color: var(--text-primary);
  line-height: 1.6;
}

.translation-content {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.detail-stats {
  margin-top: 16px;
}

@media (max-width: 1024px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-select,
  .search-input {
    flex: 1;
    min-width: 120px;
  }
}

@media (max-width: 640px) {
  .filter-group {
    flex-direction: column;
  }
  
  .filter-select,
  .search-input {
    width: 100%;
  }
  
  .post-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .post-stats {
    flex-wrap: wrap;
    gap: 12px;
  }
}

.post-translation {
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1));
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

.translation-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--accent-primary);
  font-weight: 600;
  text-transform: uppercase;
}

.post-translation p {
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
  font-style: italic;
}

.pagination-wrapper .el-pagination {
  --el-pagination-bg-color: var(--bg-card);
  --el-pagination-text-color: var(--text-primary);
  --el-pagination-button-bg-color: var(--bg-card);
  --el-pagination-hover-color: var(--accent-primary);
  font-family: inherit;
}

.pagination-wrapper .el-pagination .el-pager li {
  background: var(--bg-card);
  color: var(--text-primary);
}

.pagination-wrapper .el-pagination .el-pager li:hover {
  color: var(--accent-primary);
}

.pagination-wrapper .el-pagination .el-pager li.is-active {
  background: var(--accent-primary);
  color: #fff;
}

.pagination-wrapper .el-pagination .btn-prev,
.pagination-wrapper .el-pagination .btn-next {
  background: var(--bg-card);
  color: var(--text-primary);
}

.pagination-wrapper .el-pagination .btn-prev:hover,
.pagination-wrapper .el-pagination .btn-next:hover {
  color: var(--accent-primary);
}

.pagination-wrapper .el-pagination__sizes .el-input .el-input__wrapper {
  background: var(--bg-card);
}
</style>
