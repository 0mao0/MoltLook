<template>
  <div v-if="inline" class="agent-detail-panel">
    <div v-if="loading && !agent" class="detail-loading">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="agent" class="agent-detail">
      <div class="detail-header">
        <div class="detail-avatar">
          <el-icon size="32"><User /></el-icon>
        </div>
        <div class="detail-title">
          <div class="detail-name">{{ displayName }}</div>
          <div class="detail-id">{{ agent.id }}</div>
        </div>
        <div class="detail-risk-badge">
          <el-tag :type="riskType" effect="dark" size="large">
            {{ riskLabel() }}
          </el-tag>
        </div>
        <el-button 
          type="primary" 
          size="small"
          :loading="analyzing"
          @click="handleAnalyze"
          class="ai-analyze-btn"
        >
          <el-icon><MagicStick /></el-icon>
          {{ $t('agents.aiAnalyze') }}
        </el-button>
      </div>
      
      <div v-if="analysisResult" class="detail-card analysis-card">
        <div class="section-title">
          <el-icon><MagicStick /></el-icon>
          {{ $t('agents.aiAnalysisResult') }}
        </div>
        <div class="section-content analysis-content">
          {{ analysisResult }}
        </div>
      </div>
      
      <div class="detail-card stats-card">
        <div class="card-glow"></div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon danger">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getDangerIndex(props.agent) }}/100</div>
              <div class="stat-label">危险指数</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon conspiracy">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ (agent.avg_conspiracy_7d || 0).toFixed(1) }}</div>
              <div class="stat-label">{{ $t('dashboard.avgConspiracy') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon posts">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.post_count || 0 }}</div>
              <div class="stat-label">{{ $t('common.posts') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon replies">
              <el-icon><ChatLineRound /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.reply_count || 0 }}</div>
              <div class="stat-label">{{ $t('common.replies') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon community">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.community_id ?? '-' }}</div>
              <div class="stat-label">{{ $t('common.community') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-card info-card">
        <div class="info-row">
          <div class="info-label">{{ $t('common.firstSeen') }}</div>
          <div class="info-value">{{ formattedFirstSeen }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">{{ $t('common.lastActive') }}</div>
          <div class="info-value">{{ formattedLastActive }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">{{ $t('common.beReplied') }}</div>
          <div class="info-value">{{ agent.be_replied_count || 0 }}</div>
        </div>
      </div>

      <div v-if="agent.description" class="detail-card description-card">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          {{ $t('common.description') }}
        </div>
        <div class="section-content">{{ agent.description }}</div>
      </div>

      <div class="detail-card posts-card">
        <div class="section-title">
          <el-icon><ChatLineRound /></el-icon>
          {{ $t('common.recentPosts') }}
          <el-tag v-if="highRiskPosts.length" type="danger" size="small" effect="dark" class="high-risk-badge">
            {{ $t('agents.highRiskCount', { count: highRiskPosts.length }) }}
          </el-tag>
        </div>
        <div v-if="agent.recent_posts?.length" class="recent-posts">
          <div 
            v-for="post in agent.recent_posts" 
            :key="post.id" 
            class="recent-post-item"
            :class="postRiskLevel(post)"
          >
            <div class="post-item-content">{{ post.content }}</div>
            <div class="post-item-footer">
              <span class="post-item-time">{{ formattedPostTime(post.created_at) }}</span>
              <div class="post-item-badges">
                <span class="post-item-badge risk" :class="postRiskLevel(post)">
                  {{ riskLabel(postRiskLevel(post)) }}
                </span>
                <span class="post-item-badge score">
                  {{ $t('common.score') }} {{ (post.conspiracy_score || 0).toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-detail">
          <el-icon><Box /></el-icon>
          <span>{{ $t('agents.noPosts') }}</span>
        </div>
      </div>

      <div class="detail-card connections-card">
        <div class="section-title">
          <el-icon><Connection /></el-icon>
          {{ $t('common.connections') }}
        </div>
        <div v-if="agent.connections?.length" class="connections">
          <div v-for="item in agent.connections" :key="item.agent_id" class="connection-item">
            <div class="connection-avatar">
              <el-icon><User /></el-icon>
            </div>
            <div class="connection-info">
              <div class="connection-name">{{ connectionName(item.agent_id) }}</div>
              <div class="connection-id">{{ item.agent_id }}</div>
            </div>
            <div class="connection-count">{{ item.count }}</div>
          </div>
        </div>
        <div v-else class="empty-detail">
          <el-icon><Box /></el-icon>
          <span>{{ $t('agents.noConnections') }}</span>
        </div>
      </div>
    </div>
    <div v-else class="detail-empty">
      <el-icon><Box /></el-icon>
      <span>{{ $t('common.selectAgent') || '请选择一个 Agent' }}</span>
    </div>
  </div>
  <el-dialog
    v-else
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :title="$t('agents.detailTitle')"
    :width="dialogWidth"
    destroy-on-close
    class="agent-detail-dialog"
  >
    <div v-if="loading && !agent" class="detail-loading">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="agent" class="agent-detail">
      <div class="detail-header">
        <div class="detail-avatar">
          <el-icon size="32"><User /></el-icon>
        </div>
        <div class="detail-title">
          <div class="detail-name">{{ displayName }}</div>
          <div class="detail-id">{{ agent.id }}</div>
        </div>
        <div class="detail-risk-badge">
          <el-tag :type="riskType" effect="dark" size="large">
            {{ riskLabel() }}
          </el-tag>
        </div>
        <el-button 
          type="primary" 
          size="small"
          :loading="analyzing"
          @click="handleAnalyze"
          class="ai-analyze-btn"
        >
          <el-icon><MagicStick /></el-icon>
          {{ $t('agents.aiAnalyze') }}
        </el-button>
      </div>
      
      <div v-if="analysisResult" class="detail-card analysis-card">
        <div class="section-title">
          <el-icon><MagicStick /></el-icon>
          {{ $t('agents.aiAnalysisResult') }}
        </div>
        <div class="section-content analysis-content">
          {{ analysisResult }}
        </div>
      </div>
      
      <div class="detail-card stats-card">
        <div class="card-glow"></div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon danger">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getDangerIndex(props.agent) }}/100</div>
              <div class="stat-label">危险指数</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon conspiracy">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ (agent.avg_conspiracy_7d || 0).toFixed(1) }}</div>
              <div class="stat-label">{{ $t('dashboard.avgConspiracy') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon posts">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.post_count || 0 }}</div>
              <div class="stat-label">{{ $t('common.posts') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon replies">
              <el-icon><ChatLineRound /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.reply_count || 0 }}</div>
              <div class="stat-label">{{ $t('common.replies') }}</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon community">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ agent.community_id ?? '-' }}</div>
              <div class="stat-label">{{ $t('common.community') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-card info-card">
        <div class="info-row">
          <div class="info-label">{{ $t('common.firstSeen') }}</div>
          <div class="info-value">{{ formattedFirstSeen }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">{{ $t('common.lastActive') }}</div>
          <div class="info-value">{{ formattedLastActive }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">{{ $t('common.beReplied') }}</div>
          <div class="info-value">{{ agent.be_replied_count || 0 }}</div>
        </div>
      </div>

      <div v-if="agent.description" class="detail-card description-card">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          {{ $t('common.description') }}
        </div>
        <div class="section-content">{{ agent.description }}</div>
      </div>

      <div class="detail-card posts-card">
        <div class="section-title">
          <el-icon><ChatLineRound /></el-icon>
          {{ $t('common.recentPosts') }}
          <el-tag v-if="highRiskPosts.length" type="danger" size="small" effect="dark" class="high-risk-badge">
            {{ $t('agents.highRiskCount', { count: highRiskPosts.length }) }}
          </el-tag>
        </div>
        <div v-if="agent.recent_posts?.length" class="recent-posts">
          <div 
            v-for="post in agent.recent_posts" 
            :key="post.id" 
            class="recent-post-item"
            :class="postRiskLevel(post)"
          >
            <div class="post-item-content">{{ post.content }}</div>
            <div class="post-item-footer">
              <span class="post-item-time">{{ formattedPostTime(post.created_at) }}</span>
              <div class="post-item-badges">
                <span class="post-item-badge risk" :class="postRiskLevel(post)">
                  {{ riskLabel(postRiskLevel(post)) }}
                </span>
                <span class="post-item-badge score">
                  {{ $t('common.score') }} {{ (post.conspiracy_score || 0).toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-detail">
          <el-icon><Box /></el-icon>
          <span>{{ $t('agents.noPosts') }}</span>
        </div>
      </div>

      <div class="detail-card connections-card">
        <div class="section-title">
          <el-icon><Connection /></el-icon>
          {{ $t('common.connections') }}
        </div>
        <div v-if="agent.connections?.length" class="connections">
          <div v-for="item in agent.connections" :key="item.agent_id" class="connection-item">
            <div class="connection-avatar">
              <el-icon><User /></el-icon>
            </div>
            <div class="connection-info">
              <div class="connection-name">{{ connectionName(item.agent_id) }}</div>
              <div class="connection-id">{{ item.agent_id }}</div>
            </div>
            <div class="connection-count">{{ item.count }}</div>
          </div>
        </div>
        <div v-else class="empty-detail">
          <el-icon><Box /></el-icon>
          <span>{{ $t('agents.noConnections') }}</span>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { User, TrendCharts, Document, ChatLineRound, Connection, Box, MagicStick, Warning } from '@element-plus/icons-vue'
import { useLanguageStore } from '@/stores/language'
import { riskLabels } from '@/locales'
import { agentsApi } from '@/api'

interface Agent {
  id: string
  name?: string
  avg_conspiracy_7d?: number
  post_count?: number
  reply_count?: number
  pagerank_score?: number
  community_id?: number
  risk_level?: string
  first_seen?: number
  last_active?: number
  be_replied_count?: number
  description?: string
  recent_posts?: any[]
  connections?: any[]
}

interface Props {
  visible?: boolean
  agent?: Agent | null
  loading?: boolean
  inline?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  agent: null,
  loading: false,
  inline: false
})

const emit = defineEmits<{
  (e: 'update:visible', visible: boolean): void
}>()

const languageStore = useLanguageStore()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const onDialogVisibleChange = (val: boolean) => {
  emit('update:visible', val)
}

/**
 * 对话框宽度 - 根据屏幕宽度动态调整
 */
const dialogWidth = computed(() => {
  if (typeof window === 'undefined') return '800px'
  const screenWidth = window.innerWidth
  if (screenWidth <= 480) return '95vw'
  if (screenWidth <= 768) return '90vw'
  return '800px'
})

/**
 * 判断字符串是否为 UUID 格式
 */
const isUuid = (value: string): boolean => {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)
}

/**
 * 从 ID 中合成 Agent 展示名称
 */
const composeAgentName = (id: string): string => {
  const parts = id.split('-')
  const suffix = parts.length >= 2 ? parts.slice(-2).join('') : id
  const clean = suffix.replace(/[^a-zA-Z0-9]/g, '')
  const token = clean.length >= 6 ? clean.substring(0, 6) : id.substring(0, 6)
  return `Agent-${token}`
}

/**
 * Agent 展示名称
 */
const displayName = computed(() => {
  if (!props.agent) return ''
  const name = (props.agent.name || '').trim()
  if (name && !isUuid(name)) return name
  const id = (props.agent.id || name || '').trim()
  if (!id) return ''
  return composeAgentName(id)
})

/**
 * 风险等级类型
 */
const riskType = computed(() => {
  if (!props.agent) return 'info'
  const level = getRiskLevel(props.agent)
  const types: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return types[level] || 'info'
})

/**
 * 风险等级展示标签
 */
const riskLabel = (level?: string): string => {
  const lvl = level || getRiskLevel(props.agent)
  if (!lvl) return ''
  const label = riskLabels[lvl]
  return label 
    ? (languageStore.locale === 'zh' ? label.zh : label.en) 
    : lvl
}

/**
 * 获取 Agent 风险等级
 */
const getRiskLevel = (agent?: Agent | null): string => {
  if (!agent) return 'low'
  const score = Number(agent.avg_conspiracy_7d)
  if (Number.isFinite(score)) {
    if (score >= 10) return 'critical'
    if (score >= 8) return 'high'
    if (score >= 4) return 'medium'
    return 'low'
  }
  const raw = (agent.risk_level || '').trim()
  if (raw) return raw
  return 'low'
}

/**
 * 计算 Agent 的危险指数（0-100）
 * 危险指数 = 阴谋指数(50分) + 影响力(30分) + 互动数量(20分)
 * @param agent Agent 对象
 */
const getDangerIndex = (agent?: Agent | null): number => {
  if (!agent) return 0
  
  const avg_conspiracy = Number(agent.avg_conspiracy_7d ?? 0)
  const pagerank = Number(agent.pagerank_score ?? 0)
  const post_count = Number(agent.post_count ?? 0)
  
  // avg_conspiracy_7d 的范围是 0-10，需要归一化到 0-5
  const conspiracy_score = avg_conspiracy / 2 * 10
  const pagerank_score = pagerank * 50
  const interaction_score = Math.min(20, Math.sqrt(post_count) * 3)
  
  return Math.round(conspiracy_score + pagerank_score + interaction_score)
}

/**
 * 获取帖子风险等级
 */
const postRiskLevel = (post: any): string => {
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
 * 格式化时间戳
 */
const formatTime = (timestamp?: number): string => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString(languageStore.locale === 'zh' ? 'zh-CN' : 'en-US')
  } catch {
    return '-'
  }
}

/**
 * 格式化后的时间
 */
const formattedFirstSeen = computed(() => formatTime(props.agent?.first_seen))
const formattedLastActive = computed(() => formatTime(props.agent?.last_active))
const formattedPostTime = (timestamp?: number) => formatTime(timestamp)

/**
 * 高风险帖子
 */
const highRiskPosts = computed(() => {
  const posts = props.agent?.recent_posts || []
  return posts.filter((post: any) => {
    const level = postRiskLevel(post)
    return level === 'high' || level === 'critical'
  })
})

/**
 * 连接名称
 */
const connectionName = (id: string): string => {
  if (!id) return ''
  return composeAgentName(id)
}

/**
 * AI 分析状态
 */
const analyzing = ref(false)
const analysisResult = ref('')

/**
 * 执行 AI 分析
 */
const handleAnalyze = async () => {
  if (!props.agent?.id) return
  
  analyzing.value = true
  analysisResult.value = ''
  
  try {
    const response = await agentsApi.analyzeAgent(props.agent.id)
    analysisResult.value = response.data.analysis || '未能获取分析结果'
  } catch (error: any) {
    console.error('AI analysis failed:', error)
    analysisResult.value = error.response?.data?.detail || '分析失败，请稍后重试'
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.detail-loading {
  padding: 20px;
}

.agent-detail-panel {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.detail-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
  padding: 24px 16px;
}

.detail-empty :deep(svg) {
  width: 36px;
  height: 36px;
  opacity: 0.4;
}

.agent-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.detail-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-title {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.detail-id {
  font-size: 11px;
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
}

.detail-risk-badge {
  flex-shrink: 0;
  height: 32px;
  display: flex;
  align-items: center;
}

.ai-analyze-btn {
  flex-shrink: 0;
  margin-left: 8px;
  height: 32px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  border: none !important;
  font-weight: 600;
}

.ai-analyze-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.detail-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px 16px;
  position: relative;
}

.stats-card {
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
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
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.danger {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.stat-icon.conspiracy {
  background: rgba(124, 58, 237, 0.15);
  color: #8b5cf6;
}

.stat-icon.posts {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
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
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.info-card {
  padding: 0;
  overflow: hidden;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.section-title :deep(svg) {
  width: 16px;
  height: 16px;
}

.high-risk-badge {
  margin-left: auto;
}

.section-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.analysis-card {
  border-left: 4px solid var(--accent-primary);
}

.analysis-content {
  color: var(--text-primary);
  font-weight: 500;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1)) !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

.recent-posts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recent-post-item {
  padding: 12px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.recent-post-item:hover {
  border-color: rgba(59, 130, 246, 0.5);
  background: var(--bg-card-hover);
  transform: translateX(4px);
}

.recent-post-item.critical, 
.recent-post-item.high {
  border-left: 4px solid #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.recent-post-item.medium {
  border-left: 4px solid #f59e0b;
}

.recent-post-item.low {
  border-left: 4px solid #10b981;
}

.post-item-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.post-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.post-item-time {
  font-size: 11px;
  color: var(--text-muted);
}

.post-item-badges {
  display: flex;
  gap: 6px;
}

.post-item-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.post-item-badge.risk {
  background: rgba(75, 85, 99, 0.3);
  color: var(--text-secondary);
}

.post-item-badge.risk.critical,
.post-item-badge.risk.high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.post-item-badge.risk.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.post-item-badge.risk.low {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.post-item-badge.score {
  background: rgba(59, 130, 246, 0.15);
  color: var(--accent-primary);
}

.connections {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  transition: all 0.2s ease;
}

.connection-item:hover {
  border-color: rgba(59, 130, 246, 0.5);
  background: var(--bg-card-hover);
  transform: translateX(4px);
}

.connection-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  flex-shrink: 0;
}

.connection-avatar :deep(svg) {
  width: 16px;
  height: 16px;
}

.connection-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.connection-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.connection-id {
  font-size: 10px;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.connection-count {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-primary);
  flex-shrink: 0;
}

.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  color: var(--text-muted);
  font-size: 12px;
}

.empty-detail :deep(svg) {
  width: 36px;
  height: 36px;
  opacity: 0.4;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-header {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .detail-title {
    align-items: center;
  }
  
  .detail-risk-badge {
    width: 100%;
    display: flex;
    justify-content: center;
  }
  
  .ai-analyze-btn {
    width: 100%;
  }
  
  .info-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .info-value {
    text-align: center;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    padding: 12px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
  }
  
  .stat-icon :deep(svg) {
    width: 20px;
    height: 20px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .section-title {
    font-size: 14px;
  }
  
  .post-item-content {
    font-size: 13px;
  }
  
  .post-item-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  
  .post-item-badges {
    flex-wrap: wrap;
  }
}
</style>

<style>
.el-dialog.agent-detail-dialog {
  background: var(--bg-secondary) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-color) !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.el-dialog.agent-detail-dialog .el-dialog__header {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.15)) !important;
  border-bottom: 1px solid var(--border-color) !important;
  padding: 16px 20px;
}

.el-dialog.agent-detail-dialog .el-dialog__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary) !important;
}

.el-dialog.agent-detail-dialog .el-dialog__body {
  padding: 16px 20px;
  max-height: 75vh;
  overflow-y: auto;
  background: var(--bg-secondary) !important;
}

@media (max-width: 768px) {
  .el-dialog.agent-detail-dialog .el-dialog__header {
    padding: 12px 16px;
  }
  
  .el-dialog.agent-detail-dialog .el-dialog__body {
    padding: 12px 16px;
  }
}

@media (max-width: 480px) {
  .el-dialog.agent-detail-dialog .el-dialog__header {
    padding: 12px;
    flex-direction: column;
    gap: 8px;
  }
  
  .el-dialog.agent-detail-dialog .el-dialog__title {
    font-size: 14px;
  }
  
  .el-dialog.agent-detail-dialog .el-dialog__body {
    padding: 12px;
  }
}

.el-dialog.agent-detail-dialog .el-dialog__body::-webkit-scrollbar {
  width: 6px;
}

.el-dialog.agent-detail-dialog .el-dialog__body::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.el-dialog.agent-detail-dialog .el-dialog__body::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.6);
  border-radius: 3px;
}

.el-dialog.agent-detail-dialog .el-dialog__body::-webkit-scrollbar-thumb:hover {
  background: rgba(75, 85, 99, 0.8);
}

.el-dialog.agent-detail-dialog .el-dialog__headerbtn {
  color: var(--text-muted);
}

.el-dialog.agent-detail-dialog .el-dialog__headerbtn:hover {
  color: var(--text-primary);
}

.el-dialog.agent-detail-dialog .el-dialog__close {
  color: inherit;
}
</style>
