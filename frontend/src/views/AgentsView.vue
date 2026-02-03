<template>
  <div class="agents">
    <div v-if="isLoading && validAgents.length === 0" class="loading-container">
      <el-icon class="loading-spinner"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <template v-else>
      <div v-if="validAgents.length === 0" class="empty-container">
        <el-empty description="暂无数据">
        </el-empty>
      </div>

      <template v-else>
        <div class="risk-stats-grid">
          <div class="risk-stat-card low" :class="{ active: riskFilter === 'low' }" @click="setRiskFilter('low')">
            <div class="risk-count">{{ riskStats.low }}</div>
            <div class="risk-label">低风险 ({{ riskStats.low }})</div>
          </div>
          <div class="risk-stat-card medium" :class="{ active: riskFilter === 'medium' }" @click="setRiskFilter('medium')">
            <div class="risk-count">{{ riskStats.medium }}</div>
            <div class="risk-label">中风险 ({{ riskStats.medium }})</div>
          </div>
          <div class="risk-stat-card high" :class="{ active: riskFilter === 'high' }" @click="setRiskFilter('high')">
            <div class="risk-count">{{ riskStats.high }}</div>
            <div class="risk-label">高风险 ({{ riskStats.high }})</div>
          </div>
          <div class="risk-stat-card critical" :class="{ active: riskFilter === 'critical' }" @click="setRiskFilter('critical')">
            <div class="risk-count">{{ riskStats.critical }}</div>
            <div class="risk-label">极高风险 ({{ riskStats.critical }})</div>
          </div>
        </div>

        <div class="table-card">
          <div class="table-header">
            <div class="table-title">
              <el-icon><User /></el-icon>
              <span>Agent 列表</span>
            </div>
          </div>
          
          <div class="agent-table">
            <div class="table-header-row">
              <div class="table-cell name-cell">Agent 名称</div>
              <div class="table-cell risk-cell">风险等级</div>
              <div class="table-cell score-cell">阴谋指数</div>
              <div class="table-cell count-cell">发帖数</div>
              <div class="table-cell time-cell">最后活跃</div>
              <div class="table-cell action-cell">操作</div>
            </div>
            
            <div 
              v-for="agent in filteredAgents" 
              :key="agent.id" 
              class="table-row"
            >
              <div class="table-cell name-cell">
                <div class="agent-name">
                  <el-avatar :size="32" class="agent-avatar">
                    {{ getAvatarText(agent) }}
                  </el-avatar>
                  <span>{{ getDisplayName(agent) }}</span>
                </div>
              </div>
              <div class="table-cell risk-cell">
                <el-tag :type="getRiskType(agent.risk_level)" effect="dark" size="small">
                  {{ getRiskLabel(agent.risk_level) }}
                </el-tag>
              </div>
              <div class="table-cell score-cell">
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (agent.avg_conspiracy_7d || 0) * 10 + '%' }"></div>
                  <span class="score-text">{{ (agent.avg_conspiracy_7d || 0).toFixed(1) }}/10</span>
                </div>
              </div>
              <div class="table-cell count-cell">{{ agent.post_count || 0 }}</div>
              <div class="table-cell time-cell">{{ formatTime(agent.last_active) }}</div>
              <div class="table-cell action-cell">
                <button type="button" class="action-link" @click="viewAgentDetail(agent)">
                  详情
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>

  <el-dialog
    v-model="detailDialogVisible"
    title="Agent 详情"
    width="720px"
    destroy-on-close
  >
    <div v-if="detailLoading" class="detail-loading">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="selectedAgent" class="agent-detail">
      <div class="detail-header">
        <el-avatar :size="48" class="agent-avatar">
          {{ getAvatarText(selectedAgent) }}
        </el-avatar>
        <div class="detail-title">
          <div class="detail-name">{{ getDisplayName(selectedAgent) }}</div>
          <div class="detail-id">{{ selectedAgent.id }}</div>
        </div>
      </div>
      
      <div class="detail-card">
        <el-descriptions :column="2" border class="detail-stats">
          <el-descriptions-item label="风险等级">
            <el-tag :type="getRiskType(selectedAgent.risk_level)" effect="dark">
              {{ getRiskLabel(selectedAgent.risk_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="平均阴谋指数">
            {{ (selectedAgent.avg_conspiracy_7d || 0).toFixed(1) }}/10
          </el-descriptions-item>
          <el-descriptions-item label="发帖数">
            {{ selectedAgent.post_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="回复数">
            {{ selectedAgent.reply_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="被回复数">
            {{ selectedAgent.be_replied_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="社区">
            {{ selectedAgent.community_id ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="首次出现">
            {{ formatTime(selectedAgent.first_seen) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后活跃">
            {{ formatTime(selectedAgent.last_active) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="selectedAgent.description" class="detail-card detail-section">
        <div class="section-title">描述</div>
        <div class="section-content">{{ selectedAgent.description }}</div>
      </div>

      <div class="detail-card detail-section">
        <div class="section-title">
          最近发言
          <el-tag v-if="highRiskPosts.length" type="danger" size="small" effect="dark" style="margin-left: 8px">
            {{ highRiskPosts.length }} 条高风险
          </el-tag>
        </div>
        <div v-if="selectedAgent.recent_posts && selectedAgent.recent_posts.length" class="recent-posts">
          <div 
            v-for="post in selectedAgent.recent_posts" 
            :key="post.id" 
            class="recent-post-item"
            :class="getPostRiskLevel(post)"
          >
            <div class="post-item-content">{{ post.content }}</div>
            <div class="post-item-footer">
              <span class="post-item-time">{{ formatTime(post.created_at) }}</span>
              <div class="post-item-badges">
                <span class="post-item-badge risk" :class="getPostRiskLevel(post)">
                  {{ getRiskLabel(getPostRiskLevel(post)) }}
                </span>
                <span class="post-item-badge score">
                  阴谋指数 {{ (post.conspiracy_score || 0).toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-detail">暂无发言记录</div>
      </div>

      <div class="detail-card detail-section">
        <div class="section-title">互动对象</div>
        <div v-if="selectedAgent.connections?.length" class="connections">
          <div v-for="item in selectedAgent.connections" :key="item.agent_id" class="connection-item">
            <span class="connection-name">{{ item.agent_id }}</span>
            <span class="connection-count">{{ item.count }}</span>
          </div>
        </div>
        <div v-else class="empty-detail">暂无记录</div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { User, Loading } from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { storeToRefs } from 'pinia'
import { agentsApi, dashboardApi } from '@/api'

const store = useDataStore()
const { agents, isLoading } = storeToRefs(store)

const validAgents = computed(() => {
  if (!Array.isArray(agents.value)) return []
  return agents.value.filter(agent => 
    agent && 
    typeof agent === 'object' && 
    agent.id
  )
})

const riskStats = ref({ low: 0, medium: 0, high: 0, critical: 0 })
const detailDialogVisible = ref(false)
const selectedAgent = ref<any>(null)
const detailLoading = ref(false)
const riskFilter = ref('')
let refreshInterval: number | undefined
const filteredAgents = computed(() => {
  if (!riskFilter.value) return validAgents.value
  return validAgents.value.filter(agent => {
    const level = getAgentRiskLevel(agent)
    return level === riskFilter.value
  })
})
const highRiskPosts = computed(() => {
  const posts = selectedAgent.value?.recent_posts || []
  return posts.filter((post: any) => {
    const level = getPostRiskLevel(post)
    return level === 'high' || level === 'critical'
  })
})

/**
 * 获取 Agent 风险等级
 */
const getAgentRiskLevel = (agent: any) => {
  if (!agent) return 'low'
  const raw = (agent.risk_level || '').trim()
  if (raw) return raw
  const score = Number(agent.avg_conspiracy_7d ?? 0)
  if (score >= 7) return 'critical'
  if (score >= 4) return 'high'
  if (score >= 2) return 'medium'
  return 'low'
}

/**
 * 获取帖子风险等级
 */
const getPostRiskLevel = (post: any) => {
  if (!post) return 'low'
  const raw = (post.risk_level || '').trim()
  if (raw) return raw
  const score = Number(post.conspiracy_score ?? 0)
  if (score >= 7) return 'critical'
  if (score >= 4) return 'high'
  if (score >= 2) return 'medium'
  return 'low'
}

/**
 * 判断是否为 UUID 格式
 */
const isUuid = (value: string) => {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)
}

/**
 * 合成 Agent 展示名称
 */
const composeAgentName = (id: string) => {
  const parts = id.split('-')
  const suffix = parts.length >= 2 ? parts.slice(-2).join('') : id
  const clean = suffix.replace(/[^a-zA-Z0-9]/g, '')
  const token = clean.length >= 6 ? clean.substring(0, 6) : id.substring(0, 6)
  return `Agent-${token}`
}

/**
 * 获取 Agent 展示名称
 */
const getDisplayName = (agent: any) => {
  if (!agent) return 'Unknown'
  const name = (agent.name || '').trim()
  if (name && !isUuid(name)) return name
  const id = (agent.id || name || '').trim()
  if (!id) return 'Unknown'
  return composeAgentName(id)
}

/**
 * 获取头像文字
 */
const getAvatarText = (agent: any) => {
  const displayName = getDisplayName(agent)
  return displayName.charAt(0) || '?'
}

const getRiskType = (level: string | undefined): string => {
  if (!level) return 'info'
  const types: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return types[level] || 'info'
}

const getRiskLabel = (level: string | undefined): string => {
  if (!level) return '未知'
  const labels: Record<string, string> = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险',
    'critical': '极高风险'
  }
  return labels[level] || level
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: number | undefined): string => {
  if (!timestamp) return '从未'
  try {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('zh-CN')
  } catch {
    return '无效时间'
  }
}

/**
 * 拉取风险分布数据
 */
const fetchRiskStats = async () => {
  try {
    const res = await agentsApi.getAgentStats()
    const data = res.data || { low: 0, medium: 0, high: 0, critical: 0 }
    riskStats.value = {
      low: data.low || 0,
      medium: data.medium || 0,
      high: data.high || 0,
      critical: data.critical || 0
    }
  } catch (error) {
    console.error('Failed to fetch agent stats:', error)
    riskStats.value = { low: 0, medium: 0, high: 0, critical: 0 }
  }
}

/**
 * 查看 Agent 详情
 */
const viewAgentDetail = async (agent: any) => {
  if (!agent?.id) return
  detailDialogVisible.value = true
  detailLoading.value = true
  selectedAgent.value = null
  try {
    const res = await agentsApi.getAgent(agent.id)
    selectedAgent.value = res.data
  } catch (error) {
    selectedAgent.value = agent
  } finally {
    detailLoading.value = false
  }
}

/**
 * 刷新 Agent 列表
 */
const refreshAgents = async () => {
  await store.fetchAgents()
  await fetchRiskStats()
}

const setRiskFilter = (level: string) => {
  riskFilter.value = riskFilter.value === level ? '' : level
}

onMounted(() => {
  if (validAgents.value.length === 0) {
    refreshAgents()
  }
  fetchRiskStats()
  refreshInterval = window.setInterval(refreshAgents, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.agents {
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
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
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--text-secondary);
  font-size: 16px;
}

.loading-spinner {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-container {
  padding: 60px;
}

.risk-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

/* 即使在较小屏幕上也保持 4 列，除非非常窄 */
@media (max-width: 768px) {
  .risk-stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }
  
  .risk-stat-card {
    padding: 12px 8px;
  }
  
  .risk-count {
    font-size: 20px;
  }
  
  .risk-label {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .risk-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.risk-stat-card {
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.2s ease;
}

.risk-stat-card:hover {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.risk-stat-card.active {
  border-color: rgba(59, 130, 246, 0.7);
  box-shadow: 0 10px 24px rgba(59, 130, 246, 0.2);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(6, 182, 212, 0.12));
}

.risk-stat-card.low {
  border-left: 4px solid #10b981;
}

.risk-stat-card.medium {
  border-left: 4px solid #f59e0b;
}

.risk-stat-card.high {
  border-left: 4px solid #ef4444;
}

.risk-count {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.risk-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.table-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.table-title :deep(svg) {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.refresh-btn .btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.refresh-btn-native {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.refresh-btn-native.small {
  padding: 6px 12px;
  font-size: 13px;
}

.refresh-btn-native .btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.action-link {
  background: none;
  border: none;
  color: var(--accent-primary);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.action-link:hover {
  background: var(--accent-primary);
  color: white;
}

.agent-table {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.table-header-row {
  display: flex;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.table-row {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: var(--bg-hover);
}

.table-cell {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--text-primary);
}

.name-cell {
  flex: 1.2;
  min-width: 180px;
}

.risk-cell {
  width: 100px;
  flex-shrink: 0;
}

.score-cell {
  width: 130px;
  flex-shrink: 0;
}

.count-cell {
  width: 80px;
  flex-shrink: 0;
}

.time-cell {
  width: 160px;
  flex-shrink: 0;
}

.action-cell {
  width: 80px;
  flex-shrink: 0;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-avatar {
  background: var(--accent-primary);
  color: white;
  font-weight: 600;
}

.detail-loading {
  padding: 16px 0;
}

.agent-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.detail-id {
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-stats {
  width: 100%;
}

.detail-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-content {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.recent-posts {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-post-item {
  padding: 16px;
  border-radius: 12px;
  background: rgba(31, 41, 55, 0.4);
  border: 1px solid rgba(75, 85, 99, 0.2);
  transition: all 0.2s ease;
}

.recent-post-item:hover {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(31, 41, 55, 0.6);
}

.recent-post-item.critical, .recent-post-item.high {
  border-left: 4px solid #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.recent-post-item.medium {
  border-left: 4px solid #f59e0b;
}

.recent-post-item.low {
  border-left: 4px solid #10b981;
}

.post-item-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.post-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.post-item-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.post-item-badges {
  display: flex;
  gap: 8px;
}

.post-item-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.post-item-badge.risk.critical, .post-item-badge.risk.high {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.post-item-badge.risk.medium {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}

.post-item-badge.risk.low {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.post-item-badge.score {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.connections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}

.connection-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  font-size: 13px;
  color: var(--text-primary);
}

.connection-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.connection-count {
  font-weight: 600;
  color: var(--accent-primary);
}

.empty-detail {
  font-size: 13px;
  color: var(--text-secondary);
}

.score-bar {
  position: relative;
  height: 20px;
  background: rgba(75, 85, 99, 0.3);
  border-radius: 10px;
  overflow: hidden;
  width: 100px;
}

.score-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.score-text {
  position: relative;
  z-index: 1;
  display: block;
  text-align: center;
  line-height: 20px;
  font-size: 12px;
  color: var(--text-primary);
}

.time-value {
  color: var(--text-secondary);
  font-size: 13px;
}

@media (max-width: 1024px) {
  .page-title {
    font-size: 24px;
  }
  
  .risk-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .table-card {
    padding: 16px;
  }
  
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }
  
  .table-header-row {
    display: none;
  }
  
  .table-row {
    flex-direction: column;
    padding: 12px;
    gap: 8px;
  }
  
  .table-cell {
    width: 100% !important;
    padding: 4px 0;
  }
  
  .name-cell::before {
    content: '名称';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .risk-cell::before {
    content: '风险';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .score-cell::before {
    content: '阴谋指数';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .count-cell::before {
    content: '发帖';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .time-cell::before {
    content: '最后活跃';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .action-cell::before {
    content: '操作';
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
}
</style>
