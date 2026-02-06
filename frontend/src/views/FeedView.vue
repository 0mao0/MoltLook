<template>
  <div class="feed">
    <div class="filter-bar">
      <div class="filter-group">
        <div class="risk-cards-grid">
          <div 
            class="stat-card risk-card low" 
            :class="{ active: filters.riskLevel === 'low' }" 
            @click="setRisk('low')"
          >
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon green">
                <el-icon size="32"><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ t('feed.risk.low') }}</span>
                <span class="stat-value">{{ formatRiskCount('low') }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: rgb(16, 185, 129);"></div>
            </div>
          </div>
          <div 
            class="stat-card risk-card medium" 
            :class="{ active: filters.riskLevel === 'medium' }" 
            @click="setRisk('medium')"
          >
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon orange">
                <el-icon size="32"><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ t('feed.risk.medium') }}</span>
                <span class="stat-value">{{ formatRiskCount('medium') }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: rgb(245, 158, 11);"></div>
            </div>
          </div>
          <div 
            class="stat-card risk-card high" 
            :class="{ active: filters.riskLevel === 'high' }" 
            @click="setRisk('high')"
          >
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon red">
                <el-icon size="32"><CircleClose /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ t('feed.risk.high') }}</span>
                <span class="stat-value">{{ formatRiskCount('high') }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: rgb(239, 68, 68);"></div>
            </div>
          </div>
          <div 
            class="stat-card risk-card critical" 
            :class="{ active: filters.riskLevel === 'critical' }" 
            @click="setRisk('critical')"
          >
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon purple">
                <el-icon size="32"><WarningFilled /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ t('feed.risk.critical') }}</span>
                <span class="stat-value">{{ formatRiskCount('critical') }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: rgb(124, 58, 237);"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="posts-container">
      <div v-if="isLoading && posts.length === 0" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="posts.length === 0" class="empty-state">
        <el-empty :description="t('feed.empty')">
        </el-empty>
      </div>
      
      <template v-else>
        <div class="posts-list">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-card"
            :class="getPostRiskLevel(post)"
          >
            <!-- Agent 卡片 -->
            <div class="agent-badge">
              <div class="badge-prefix">
                <el-icon size="12"><UserFilled /></el-icon>
                <span>{{ t('common.agent') }}</span>
              </div>
              <div class="badge-content">
                {{ getAgentName(post) }}
              </div>
            </div>

            <div class="post-header">
              <a 
                v-if="post.title || post.url" 
                class="post-title-link" 
                :href="post.url || '#'" 
                target="_blank"
              >
                {{ post.title || t('common.viewOriginal') }}
              </a>
              <div class="risk-badge" :style="{ '--badge-color': getRiskColor(getPostRiskLevel(post)) }">
                {{ getRiskLabel(getPostRiskLevel(post)) }}
                <span class="risk-score">{{ formatPostRiskScore(post.conspiracy_score) }}</span>
              </div>
            </div>
            
            <div class="post-content">
              <p>{{ post.content }}</p>
            </div>
            
            <div v-if="post.translation" class="post-translation">
              <div class="translation-header">
                <el-icon size="14"><Edit /></el-icon>
                <span>{{ t('common.analysisResult') }}</span>
              </div>
              <p>{{ post.translation }}</p>
            </div>
            
            <div class="post-footer">
              <!-- 时间移至左下角 -->
              <span class="post-time-footer">{{ formatTime(post.created_at) }}</span>
              <button 
                type="button" 
                class="translate-btn" 
                @click="analyzePost(post)"
                :disabled="isAnalyzing(post.id)"
              >
                <span>{{ isAnalyzing(post.id) ? t('common.analyzing') : t('common.analyze') }}</span>
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
      :title="t('feed.detailTitle')"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedPost" class="post-detail">
        <div class="detail-header">
          <div class="author-meta">
            <div class="agent-badge">
              <div class="badge-prefix">
                <el-icon size="12"><UserFilled /></el-icon>
                <span>{{ t('common.agent') }}</span>
              </div>
              <div class="badge-content">
                {{ getAgentName(selectedPost) }}
              </div>
            </div>
            <span class="post-time">{{ formatTime(selectedPost.created_at) }}</span>
          </div>
        </div>
        
        <div class="detail-content">
          <h4>{{ t('common.content') }}</h4>
          <p>{{ selectedPost.content }}</p>
          
          <div v-if="selectedPost.translation" class="translation-content">
            <h4>{{ t('common.analysisResult') }}</h4>
            <p>{{ selectedPost.translation }}</p>
          </div>
        </div>
        
        <div class="detail-stats">
          <el-descriptions :column="2" border>
          <el-descriptions-item :label="t('common.riskLevel')">
            <el-tag :type="getRiskType(getPostRiskLevel(selectedPost))" effect="dark">
              {{ getRiskLabel(getPostRiskLevel(selectedPost)) }}
            </el-tag>
          </el-descriptions-item>
            <el-descriptions-item :label="t('common.score')">
              {{ (selectedPost.conspiracy_score || 0).toFixed(1) }}/10
            </el-descriptions-item>
            <el-descriptions-item :label="t('common.sentiment')">
              {{ selectedPost.sentiment !== undefined ? formatSentiment(selectedPost.sentiment) : t('common.noData') }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('common.community')">
              {{ getSubmoltLabel(selectedPost.submolt || 'general') }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Document, 
  Refresh, 
  Edit,
  Loading,
  Warning,
  UserFilled,
  CircleCheck,
  CircleClose,
  WarningFilled
} from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { translationApi, dashboardApi } from '@/api'
import { submoltLabels, riskLabels } from '@/locales'

const route = useRoute()
const { t } = useI18n()
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
const analyzedPosts = ref<Map<string, string>>(new Map())
const analyzingPosts = ref<Set<string>>(new Set())

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
 * @param level 风险等级
 */
const formatRiskCount = (level: string) => {
  const count = riskDistribution.value[level] || 0
  if ((level === 'low' || level === 'medium') && count >= 1000) {
    return t('feed.retainedLimit')
  }
  return count.toString()
}

/**
 * 获取子社区标签
 * @param key 子社区键值
 */
const getSubmoltLabel = (key: string) => {
  if (!key || !key.trim()) return t('submolt.other')
  const labels = submoltLabels[key]
  if (!labels) return t('submolt.other')
  return languageStore.locale === 'zh' ? labels.zh : labels.en
}

/**
 * 获取子社区颜色
 * @param key 子社区键值
 */
const getSubmoltColor = (key: string) => {
  if (!key || !key.trim()) return '#6b7280'
  return submoltLabels[key]?.color || '#6b7280'
}

/**
 * 获取风险等级标签
 * @param level 风险等级
 */
const getRiskLabel = (level: string) => {
  if (!level || !level.trim()) return t('common.unknown')
  const labels = riskLabels[level]
  if (!labels) return level
  return languageStore.locale === 'zh' ? labels.zh : labels.en
}

/**
 * 根据分值获取帖子风险等级
 */
const getPostRiskLevel = (post: any) => {
  if (!post) return 'low'
  const score = Number(post.conspiracy_score)
  if (Number.isFinite(score)) {
    if (score >= 10) return 'critical'
    if (score >= 8) return 'high'
    if (score >= 4) return 'medium'
    return 'low'
  }
  const raw = (post.risk_level || '').trim()
  if (raw) return raw
  return 'low'
}

/**
 * 格式化帖子风险指数
 */
const formatPostRiskScore = (score: number) => {
  const value = Number(score)
  if (!Number.isFinite(value)) return '0.0'
  return value.toFixed(1)
}

/**
 * 获取风险等级颜色
 * @param level 风险等级
 */
const getRiskColor = (level: string) => {
  if (!level || !level.trim()) return '#6b7280'
  return riskLabels[level]?.color || '#6b7280'
}

/**
 * 检查帖子是否正在分析中
 * @param postId 帖子ID
 */
const isAnalyzing = (postId: string) => {
  return analyzingPosts.value.has(postId)
}

/**
 * 获取 Agent 名称
 * @param post 帖子对象
 */
const getAgentName = (post: any) => {
  if (post.author_name && post.author_name.trim()) {
    return post.author_name
  }
  const authorId = post.author_id
  if (!authorId || authorId === 'unknown') return t('common.anonymous')
  
  if (agents.value.length > 0) {
    const agent = agents.value.find(a => a && a.id === authorId)
    if (agent && agent.name && agent.name.trim()) {
      return agent.name
    }
  }
  
  // 如果找不到名称且 authorId 是 UUID，则不显示长 ID，仅显示匿名
  if (authorId.includes('-') && authorId.length > 20) {
    return t('common.anonymous')
  }
  
  return authorId
}

/**
 * 获取风险类型对应的 Element Plus 标签类型
 * @param level 风险等级
 */
const getRiskType = (level: string) => {
  const types: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return types[level] || 'info'
}

/**
 * 获取情感倾向对应的 Element Plus 标签类型
 * @param val 情感值
 */
const getSentimentType = (val: number) => {
  if (!val && val !== 0) return 'info'
  if (val > 0.3) return 'success'
  if (val < -0.3) return 'danger'
  return 'info'
}

/**
 * 格式化情感倾向显示
 * @param val 情感值
 */
const formatSentiment = (val: number) => {
  if (!val && val !== 0) return t('sentiment.neutral')
  if (val > 0.3) return t('sentiment.positive')
  if (val < -0.3) return t('sentiment.negative')
  return t('sentiment.neutral')
}

/**
 * 格式化时间显示
 * @param timestamp 时间戳（秒）
 */
const formatTime = (timestamp: number) => {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return languageStore.locale === 'zh' 
    ? date.toLocaleString('zh-CN') 
    : date.toLocaleString('en-US')
}

/**
 * 设置风险等级筛选
 * @param level 风险等级
 */
const setRisk = (level: string) => {
  filters.value.riskLevel = level
  currentPage.value = 1
  refreshPosts()
}

/**
 * 启动自动刷新定时器
 */
const startAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  refreshInterval = setInterval(() => {
    refreshPosts()
  }, 30000)
}

/**
 * 刷新帖子列表和风险分布数据
 */
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

/**
 * 处理分页大小变化
 * @param val 分页大小
 */
const handleSizeChange = (val: number) => {
  pageSize.value = val
  refreshPosts()
}

/**
 * 处理当前页码变化
 * @param val 当前页码
 */
const handleCurrentChange = (val: number) => {
  currentPage.value = val
  refreshPosts()
}

/**
 * 查看帖子详情（如果有 URL 则在新窗口打开，否则显示详情弹窗）
 * @param post 帖子对象
 */
const viewPostDetail = (post: any) => {
  if (post.url) {
    window.open(post.url, '_blank')
  } else {
    selectedPost.value = post
    detailDialogVisible.value = true
  }
}

/**
 * 分析帖子内容（LLM 风险分析）
 * @param post 帖子对象
 */
const analyzePost = async (post: any) => {
  const cacheKey = post.id
  
  if (analyzedPosts.value.has(cacheKey)) {
    post.translation = analyzedPosts.value.get(cacheKey)
    return
  }
  
  if (analyzingPosts.value.has(cacheKey)) {
    return
  }
  
  analyzingPosts.value.add(cacheKey)
  
  try {
    const response = await translationApi.analyze(post.content, post.risk_level, languageStore.locale)
    if (response.data && response.data.analysis) {
      analyzedPosts.value.set(cacheKey, response.data.analysis)
      post.translation = response.data.analysis
    } else {
      post.translation = t('feed.analysisFailed')
    }
  } catch (error: any) {
    console.error('Analysis failed:', error)
    if (error?.code === 'ECONNABORTED' || String(error?.message || '').includes('timeout')) {
      post.translation = t('feed.translationTimeout')
      return
    }
    const errorMsg = error.response?.data?.detail || t('feed.analysisFailed')
    post.translation = errorMsg
  } finally {
    analyzingPosts.value.delete(cacheKey)
  }
}

onMounted(() => {
  const riskParam = route.query.risk as string
  if (riskParam && ['low', 'medium', 'high', 'critical'].includes(riskParam)) {
    filters.value.riskLevel = riskParam
  }
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
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
}

.risk-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  width: 100%;
}

.stat-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent-primary);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
}

.stat-card.active {
  border-color: var(--accent-primary);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.card-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.card-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.green {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.stat-icon.orange {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.stat-icon.red {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.stat-icon.purple {
  background: rgba(124, 58, 237, 0.1);
  color: #7c3aed;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.risk-indicator-bar {
  height: 4px;
  background: rgba(75, 85, 99, 0.3);
  border-radius: 2px;
  overflow: hidden;
}

.risk-level {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

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

.agent-badge {
  display: inline-flex;
  align-items: center;
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.post-card .agent-badge {
  margin-bottom: 14px;
}

.agent-badge:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  transform: translateY(-2px);
  background: rgba(30, 41, 59, 0.9);
}

.badge-prefix {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.1));
  padding: 6px 10px;
  color: #60a5fa;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border-right: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-content {
  padding: 6px 12px;
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 600;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  letter-spacing: 0.2px;
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
  gap: 6px;
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

.risk-score {
  color: #f9fafb;
  font-weight: 700;
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
  .risk-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
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
  .risk-cards-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
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
