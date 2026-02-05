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
              <div class="risk-level" style="width: 100%; background: rgb(16, 185, 129);"></div>
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
              <div class="risk-level" style="width: 100%; background: rgb(245, 158, 11);"></div>
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
              <div class="risk-level" style="width: 100%; background: rgb(239, 68, 68);"></div>
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
              <div class="risk-level" style="width: 100%; background: rgb(124, 58, 237);"></div>
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
              v-for="agent in paginatedAgents" 
              :key="agent.id" 
              class="table-row"
            >
              <div class="table-cell name-cell">
                <div class="agent-name">
                  <span>{{ getDisplayName(agent) }}</span>
                </div>
              </div>
              <div class="table-cell risk-cell">
                <span class="info-label">{{ $t('common.riskLevel') }}:</span>
                <el-tag :type="getRiskType(agent.risk_level)" effect="dark" size="small">
                  {{ getRiskLabel(agent.risk_level) }}
                </el-tag>
              </div>
              <div class="table-cell score-cell">
                <span class="info-label">{{ $t('common.score') }}:</span>
                <div class="score-bar">
                  <div 
                    class="score-fill" 
                    :class="getScoreClass(agent)"
                    :style="{ width: (getDangerIndex(agent) || 0) + '%' }"
                  ></div>
                  <span class="score-text">{{ getDangerIndex(agent) || 0 }}/100</span>
                </div>
              </div>
              <div class="table-cell count-cell">
                <span class="info-label">{{ $t('common.posts') }}:</span>
                <span>{{ agent.post_count || 0 }}</span>
              </div>
              <div class="table-cell time-cell">
                <span class="info-label">{{ $t('common.lastActive') }}:</span>
                <span class="time-value">{{ formatTime(agent.last_active) }}</span>
              </div>
              <div class="table-cell action-cell">
                <button type="button" class="action-link" @click="viewAgentDetail(agent)">
                  {{ $t('common.details') }}
                </button>
              </div>
            </div>
          </div>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="totalAgents"
              layout="prev, pager, next, jumper"
              :background="true"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </template>
    </template>
  </div>

  <AgentDetail
    v-model:visible="detailDialogVisible"
    :agent="selectedAgent"
    :loading="detailLoading"
  />
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
  WarningFilled,
  TrendCharts,
  Document,
  ChatLineRound,
  Connection,
  Box
} from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { agentsApi } from '@/api'
import { riskLabels } from '@/locales'
import AgentDetail from '@/components/AgentDetail.vue'

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
const currentPage = ref(1)
const pageSize = ref(10)
const totalAgents = ref(0)
let refreshInterval: number | undefined

/**
 * 直接使用后端返回的 Agent 列表（后端分页）
 */
const paginatedAgents = computed(() => {
  return agents.value
})

/**
 * 根据风险等级过滤后的 Agent 列表
 * 注意：由于 setRiskFilter 已经调用后端 API 获取过滤后的数据，
 * 所以这里直接返回 validAgents.value 即可
 */
const filteredAgents = computed(() => {
  return agents.value
})

/**
 * 处理分页变化
 * @param page 当前页码
 */
const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadAgentsForPage(page)
}

/**
 * 加载指定页的 Agent 数据
 * @param page 页码
 */
const loadAgentsForPage = async (page: number) => {
  try {
    const params: any = {
      page: page,
      page_size: pageSize.value
    }
    
    if (riskFilter.value) {
      params.risk_level = riskFilter.value
    }
    
    const res = await agentsApi.getAgents(params)
    const data = res.data
    
    // 处理新的响应格式 { agents: [], total: 0, page: 1, page_size: 10 }
    if (data && data.agents && Array.isArray(data.agents)) {
      agents.value = data.agents.filter((item: any) => item && item.id)
      totalAgents.value = data.total || 0
    } else if (Array.isArray(data)) {
      // 兼容旧格式
      agents.value = data.filter((item: any) => item && item.id)
      totalAgents.value = data.length
    }
  } catch (error) {
    console.error('Failed to load agents for page:', page, error)
  }
}

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
 * 计算 Agent 的危险指数（0-100）
 * 危险指数 = 阴谋指数(50分) + 影响力(30分) + 互动数量(20分)
 * @param agent Agent 对象
 */
const getDangerIndex = (agent: any): number => {
  if (!agent) return 0
  
  const avg_conspiracy = Number(agent.avg_conspiracy_7d ?? 0)
  const pagerank = Number(agent.pagerank_score ?? 0)
  const post_count = Number(agent.post_count ?? 0)
  
  const conspiracy_score = avg_conspiracy * 10
  const pagerank_score = pagerank * 50
  const interaction_score = Math.min(20, Math.sqrt(post_count) * 3)
  
  return Math.round(conspiracy_score + pagerank_score + interaction_score)
}

/**
 * 获取危险指数等级对应的CSS类
 * @param agent Agent 对象
 */
const getScoreClass = (agent: any): string => {
  const danger = getDangerIndex(agent)
  if (danger >= 70) return 'score-critical'
  if (danger >= 50) return 'score-high'
  if (danger >= 25) return 'score-medium'
  return 'score-low'
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
 * 根据 ID 获取 Agent 名称
 * @param id Agent ID
 */
const getAgentNameById = (id: string) => {
  if (!id) return t('common.unknown')
  const agent = validAgents.value.find(a => a.id === id)
  if (agent) return getDisplayName(agent)
  return composeAgentName(id)
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
  await loadAgentsForPage(currentPage.value)
  await fetchRiskStats()
}

/**
 * 设置风险等级过滤条件（点击卡片切换）
 * @param level 风险等级
 */
const setRiskFilter = async (level: string) => {
  if (riskFilter.value === level) {
    riskFilter.value = ''
  } else {
    riskFilter.value = level
  }
  // 重置到第一页并重新加载
  currentPage.value = 1
  await loadAgentsForPage(1)
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
.stats-grid, .risk-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
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
  gap: 12px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
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
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 24px;
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
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
  border-radius: 2px;
  transition: width 0.5s ease;
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
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stat-card {
    padding: 12px;
    min-height: 100px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
  }
  
  .stat-icon :deep(svg) {
    width: 24px;
    height: 24px;
  }
  
  .stat-label {
    font-size: 11px;
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
  flex: 1;
  min-width: 140px;
}

.risk-cell {
  flex: 0.8;
  min-width: 100px;
}

.score-cell {
  flex: 1;
  min-width: 100px;
}

.count-cell {
  flex: 0.6;
  min-width: 80px;
}

.time-cell {
  flex: 1;
  min-width: 140px;
}

.action-cell {
  flex: 0.6;
  min-width: 80px;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}

.info-label {
  color: var(--text-secondary);
  font-size: 12px;
}

@media (min-width: 769px) {
  .info-label {
    display: none;
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

.pagination-container :deep(.el-pagination) {
  display: flex;
  gap: 4px;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li) {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-weight: 500;
  min-width: 32px;
  height: 32px;
  line-height: 32px;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li:hover) {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
}

.pagination-container :deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  color: #ffffff;
  border-color: transparent;
}

.pagination-container :deep(.el-pagination button) {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-weight: 500;
  min-width: 32px;
  height: 32px;
}

.pagination-container :deep(.el-pagination button:hover) {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
}

.pagination-container :deep(.el-pagination button:disabled) {
  background: var(--bg-card);
  color: var(--text-secondary);
  border-color: var(--border-color);
  opacity: 0.5;
}

.pagination-container :deep(.el-pagination__jump) {
  color: var(--text-secondary);
  font-size: 14px;
}

.pagination-container :deep(.el-pagination__jump .el-input__wrapper) {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: none;
  width: 50px;
}

.pagination-container :deep(.el-pagination__jump .el-input__wrapper:hover) {
  border-color: var(--accent-primary);
}

.pagination-container :deep(.el-pagination__jump .el-input__inner) {
  color: var(--text-primary);
  text-align: center;
}

.detail-loading {
  padding: 16px 0;
}

.agent-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 弹框头部 */
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  margin-bottom: 12px;
}

.detail-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  flex-shrink: 0;
}

.detail-avatar :deep(svg) {
  width: 20px;
  height: 20px;
}

.detail-title {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.detail-name {
  font-size: 16px;
  font-weight: 700;
  color: #f9fafb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-id {
  font-size: 11px;
  color: #9ca3af;
  font-family: 'Courier New', monospace;
}

.detail-risk-badge {
  flex-shrink: 0;
}

/* 统计卡片 */
.detail-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px 16px;
  position: relative;
  overflow: hidden;
  margin-bottom: 12px;
}

.card-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.stats-card {
  padding: 12px 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.stat-icon.conspiracy {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.stat-icon.posts {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.stat-icon.replies {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.stat-icon.community {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.stat-content {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
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
  border-radius: 10px;
  transition: width 0.3s ease;
}

.score-fill.score-low {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.score-fill.score-medium {
  background: linear-gradient(90deg, #eab308, #facc15);
}

.score-fill.score-high {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.score-fill.score-critical {
  background: linear-gradient(90deg, #dc2626, #ef4444);
}

.score-text {
  position: relative;
  z-index: 1;
  display: block;
  text-align: center;
  line-height: 20px;
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
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
  
  .table-card {
    padding: 12px;
  }
  
  .agent-table {
    border: none;
    border-radius: 0;
  }
  
  .table-header-row {
    display: none;
  }
  
  .table-row {
    display: flex;
    flex-direction: column;
    padding: 16px;
    gap: 12px;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 12px;
    background: var(--bg-card);
    transition: all 0.3s ease;
  }
  
  .table-row:hover {
    background: var(--bg-card-hover);
    border-color: rgba(59, 130, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
  }
  
  .table-row:last-child {
    border-bottom: 1px solid var(--border-color);
  }
  
  .table-cell {
    width: 100% !important;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .name-cell {
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(75, 85, 99, 0.3);
    margin-bottom: 4px;
  }
  
  .name-cell .agent-name span {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .info-label {
    display: none;
  }
  
  .score-bar {
    width: 80px;
  }
  
  .time-value {
    font-size: 12px;
    color: var(--text-muted);
  }
  
  .action-cell {
    margin-top: 4px;
    padding-top: 8px;
    border-top: 1px solid rgba(75, 85, 99, 0.3);
  }
  
  .action-link {
    width: 100%;
    padding: 10px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.2));
    border: 1px solid rgba(59, 130, 246, 0.4);
    border-radius: 8px;
    font-weight: 600;
    text-align: center;
  }
  
  .action-link:hover {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
  }
}
</style>
