<template>
  <div class="agents">
    <div v-if="isLoading && validAgents.length === 0" class="loading-container">
      <el-icon class="loading-spinner"><Loading /></el-icon>
      <span>{{ $t('common.loading') }}</span>
    </div>

    <template v-else>
      <div v-if="validAgents.length === 0" class="empty-container">
        <el-empty :description="$t('common.noData')">
        </el-empty>
      </div>

      <template v-else>
        <div class="stats-grid">
          <div class="stat-card risk-card low" :class="{ active: riskFilter === 'low' }" @click="setRiskFilter('low')">
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon green">
                <el-icon size="32"><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ $t('risk.low') }}</span>
                <span class="stat-value">{{ riskStats.low }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: #10b981;"></div>
            </div>
          </div>

          <div class="stat-card risk-card medium" :class="{ active: riskFilter === 'medium' }" @click="setRiskFilter('medium')">
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon orange">
                <el-icon size="32"><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ $t('risk.medium') }}</span>
                <span class="stat-value">{{ riskStats.medium }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: #f59e0b;"></div>
            </div>
          </div>

          <div class="stat-card risk-card high" :class="{ active: riskFilter === 'high' }" @click="setRiskFilter('high')">
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon red">
                <el-icon size="32"><CircleClose /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ $t('risk.high') }}</span>
                <span class="stat-value">{{ riskStats.high }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: #ef4444;"></div>
            </div>
          </div>

          <div class="stat-card risk-card critical" :class="{ active: riskFilter === 'critical' }" @click="setRiskFilter('critical')">
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="stat-icon purple">
                <el-icon size="32"><WarningFilled /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">{{ $t('risk.critical') }}</span>
                <span class="stat-value">{{ riskStats.critical }}</span>
              </div>
            </div>
            <div class="risk-indicator-bar">
              <div class="risk-level" style="width: 100%; background: #7c3aed;"></div>
            </div>
          </div>
        </div>

        <div class="table-card">
          <div class="table-header">
            <div class="table-title">
              <el-icon><User /></el-icon>
              <span>{{ $t('agents.title') }}</span>
            </div>
          </div>
          
          <div class="agent-table">
            <div class="table-header-row">
              <div class="table-cell name-cell">{{ $t('common.agent') }}</div>
              <div class="table-cell risk-cell">{{ $t('common.riskLevel') }}</div>
              <div class="table-cell score-cell">{{ $t('common.score') }}</div>
              <div class="table-cell count-cell">{{ $t('common.posts') }}</div>
              <div class="table-cell time-cell">{{ $t('common.lastActive') }}</div>
              <div class="table-cell action-cell">{{ $t('common.details') }}</div>
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
                  {{ $t('common.details') }}
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
    :title="$t('agents.detailTitle')"
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
          <el-descriptions-item :label="$t('common.riskLevel')">
            <el-tag :type="getRiskType(selectedAgent.risk_level)" effect="dark">
              {{ getRiskLabel(selectedAgent.risk_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('dashboard.avgConspiracy')">
            {{ (selectedAgent.avg_conspiracy_7d || 0).toFixed(1) }}/10
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.posts')">
            {{ selectedAgent.post_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.replies')">
            {{ selectedAgent.reply_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.beReplied')">
            {{ selectedAgent.be_replied_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.community')">
            {{ selectedAgent.community_id ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.firstSeen')">
            {{ formatTime(selectedAgent.first_seen) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.lastActive')">
            {{ formatTime(selectedAgent.last_active) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="selectedAgent.description" class="detail-card detail-section">
        <div class="section-title">{{ $t('common.description') }}</div>
        <div class="section-content">{{ selectedAgent.description }}</div>
      </div>

      <div class="detail-card detail-section">
        <div class="section-title">
          {{ $t('common.recentPosts') }}
          <el-tag v-if="highRiskPosts.length" type="danger" size="small" effect="dark" style="margin-left: 8px">
            {{ $t('agents.highRiskCount', { count: highRiskPosts.length }) }}
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
                  {{ $t('common.score') }} {{ (post.conspiracy_score || 0).toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-detail">{{ $t('agents.noPosts') }}</div>
      </div>

      <div class="detail-card detail-section">
        <div class="section-title">{{ $t('common.connections') }}</div>
        <div v-if="selectedAgent.connections?.length" class="connections">
          <div v-for="item in selectedAgent.connections" :key="item.agent_id" class="connection-item">
            <span class="connection-name">{{ item.agent_id }}</span>
            <span class="connection-count">{{ item.count }}</span>
          </div>
        </div>
        <div v-else class="empty-detail">{{ $t('agents.noConnections') }}</div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { 
  User, 
  Loading, 
  Refresh, 
  CircleCheck, 
  Warning, 
  CircleClose, 
  WarningFilled 
} from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { agentsApi } from '@/api'
import { riskLabels } from '@/locales'

const { t } = useI18n()
const languageStore = useLanguageStore()
const store = useDataStore()
const { agents, isLoading } = storeToRefs(store)

/**
 * 过滤有效的 Agent 列表
 */
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

/**
 * 根据风险等级过滤后的 Agent 列表
 */
const filteredAgents = computed(() => {
  if (!riskFilter.value) return validAgents.value
  return validAgents.value.filter(agent => {
    const level = getAgentRiskLevel(agent)
    return level === riskFilter.value
  })
})

/**
 * 当前选中 Agent 的高风险帖子
 */
const highRiskPosts = computed(() => {
  const posts = selectedAgent.value?.recent_posts || []
  return posts.filter((post: any) => {
    const level = getPostRiskLevel(post)
    return level === 'high' || level === 'critical'
  })
})

/**
 * 获取 Agent 风险等级
 * @param agent Agent 对象
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
 * @param post 帖子对象
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
 * 判断字符串是否为 UUID 格式
 * @param value 待检查的字符串
 */
const isUuid = (value: string) => {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)
}

/**
 * 从 ID 中合成 Agent 展示名称（用于 UUID 的后几位）
 * @param id Agent ID
 */
const composeAgentName = (id: string) => {
  const parts = id.split('-')
  const suffix = parts.length >= 2 ? parts.slice(-2).join('') : id
  const clean = suffix.replace(/[^a-zA-Z0-9]/g, '')
  const token = clean.length >= 6 ? clean.substring(0, 6) : id.substring(0, 6)
  return `Agent-${token}`
}

/**
 * 获取 Agent 展示名称（优先使用 name，如果是 UUID 则合成名称）
 * @param agent Agent 对象
 */
const getDisplayName = (agent: any) => {
  if (!agent) return t('common.unknown')
  const name = (agent.name || '').trim()
  if (name && !isUuid(name)) return name
  const id = (agent.id || name || '').trim()
  if (!id) return t('common.unknown')
  return composeAgentName(id)
}

/**
 * 获取 Agent 头像展示文字（名称首字母）
 * @param agent Agent 对象
 */
const getAvatarText = (agent: any) => {
  const displayName = getDisplayName(agent)
  return displayName.charAt(0) || '?'
}

/**
 * 获取风险等级对应的 Element Plus 标签类型
 * @param level 风险等级
 */
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

/**
 * 获取风险等级展示标签（支持 i18n）
 * @param level 风险等级
 */
const getRiskLabel = (level: string | undefined): string => {
  if (!level) return t('common.unknown')
  const label = riskLabels[level]
  return label ? (languageStore.locale === 'zh' ? label.zh : label.en) : level
}

/**
 * 格式化时间戳为本地时间字符串
 * @param timestamp 时间戳（秒）
 */
const formatTime = (timestamp: number | undefined): string => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString(languageStore.locale === 'zh' ? 'zh-CN' : 'en-US')
  } catch {
    return '-'
  }
}

/**
 * 拉取风险分布统计数据
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
 * 查看 Agent 详情信息
 * @param agent Agent 对象
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
 * 刷新 Agent 列表及统计数据
 */
const refreshAgents = async () => {
  await store.fetchAgents()
  await fetchRiskStats()
}

/**
 * 设置风险等级过滤条件（点击卡片切换）
 * @param level 风险等级
 */
const setRiskFilter = (level: string) => {
  riskFilter.value = riskFilter.value === level ? '' : level
}

/**
 * 生命周期钩子：组件挂载时启动刷新
 */
onMounted(() => {
  if (validAgents.value.length === 0) {
    refreshAgents()
  }
  fetchRiskStats()
  refreshInterval = window.setInterval(refreshAgents, 30000)
})

/**
 * 生命周期钩子：组件卸载时清除定时器
 */
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

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
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
  border-color: var(--border-glow);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
}

.stat-card.active {
  border-color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.05);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
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
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent-primary);
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

.stat-icon :deep(svg) {
  width: 32px;
  height: 32px;
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

/* 风险卡片特殊样式 */
.risk-card {
  border-left: 4px solid;
}

.risk-card.low {
  border-left-color: #10b981;
}

.risk-card.medium {
  border-left-color: #f59e0b;
}

.risk-card.high {
  border-left-color: #ef4444;
}

.risk-card.critical {
  border-left-color: #7c3aed;
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

.risk-card.low .risk-level {
  background: #10b981;
}

.risk-card.medium .risk-level {
  background: #f59e0b;
}

.risk-card.high .risk-level {
  background: #ef4444;
}

.risk-card.critical .risk-level {
  background: #7c3aed;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .stat-icon {
    width: 44px;
    height: 44px;
  }
  
  .stat-icon :deep(svg) {
    width: 24px;
    height: 24px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
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
    content: var(--label-name);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .risk-cell::before {
    content: var(--label-risk);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .score-cell::before {
    content: var(--label-score);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .count-cell::before {
    content: var(--label-posts);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .time-cell::before {
    content: var(--label-time);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
  
  .action-cell::before {
    content: var(--label-action);
    color: var(--text-secondary);
    font-size: 12px;
    margin-right: 8px;
  }
}
</style>
