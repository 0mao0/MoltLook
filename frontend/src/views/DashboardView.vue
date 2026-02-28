<template>
  <div class="dashboard">
    <div class="stats-grid">
      <!-- 危险帖子卡片 -->
      <div class="stat-card danger-card" style="cursor: pointer" @click="router.push({ path: '/feed', query: { risk: 'high' } })">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon red">
            <el-icon size="32" color="#ef4444"><WarningFilled /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.dangerPosts') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.dangerous_posts) }}</span>
          </div>
        </div>
        <div class="stat-trend secondary">
          <span>{{ $t('dashboard.total') }}</span>
        </div>
      </div>

      <!-- 意见领袖卡片 -->
      <div class="stat-card" style="cursor: pointer" @click="router.push('/agents')">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon purple">
            <el-icon size="32"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.opinionLeaders') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.key_persons) }}</span>
          </div>
        </div>
        <div class="stat-trend">
          <span>{{ $t('dashboard.influential') }}</span>
        </div>
      </div>

      <!-- 高危Agent -->
      <div class="stat-card risk-card" :class="stats?.risk_level">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon">
            <el-icon size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.currentRiskLevel') }}</span>
            <span class="stat-value">{{ getRiskLabel(stats?.risk_level) }}</span>
          </div>
        </div>
        <div class="risk-indicator-bar">
          <div class="risk-level" :style="{ width: getRiskPercentage(stats?.risk_level) + '%' }"></div>
        </div>
      </div>

      <!-- 总帖子数 -->
      <div class="stat-card" style="cursor: pointer" @click="router.push('/feed')">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon blue">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.totalPosts') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.total_posts) }}</span>
          </div>
        </div>
        <div class="stat-trend">
          <span>{{ $t('dashboard.analyzed') }}: {{ formatNumber(stats?.analyzed_posts) }}</span>
        </div>
      </div>
    </div>

    <div class="dashboard-charts">
      <!-- 关系图 -->
      <NetworkGraph />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import NetworkGraph from '@/components/NetworkGraph.vue'
import { 
  Warning, 
  WarningFilled,
  Document, 
  UserFilled,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import { riskLabels } from '@/locales'

const router = useRouter()
const languageStore = useLanguageStore()
const store = useDataStore()
const { stats } = storeToRefs(store)

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

// 格式化增长率
const formatGrowthRate = (rate: number) => {
  if (rate === undefined || rate === null) return '0%'
  const sign = rate > 0 ? '+' : ''
  return `${sign}${rate.toFixed(1)}%`
}

// 获取增长率样式类
const getGrowthClass = (rate: number) => {
  if (!rate) return ''
  return rate > 0 ? 'up' : 'down'
}

// 获取风险标签
const getRiskLabel = (level: string) => {
  if (!level) return ''
  const label = riskLabels[level]
  return label ? (languageStore.locale === 'zh' ? label.zh : label.en) : level
}

// 获取风险百分比
const getRiskPercentage = (level: string) => {
  const percentages: Record<string, number> = {
    'low': 25,
    'medium': 50,
    'high': 75,
    'critical': 100
  }
  return percentages[level] || 0
}

// 刷新数据
const refreshData = async () => {
  await store.fetchDashboard()
}

// 自动刷新
let refreshInterval: number

onMounted(() => {
  refreshData()
  refreshInterval = window.setInterval(refreshData, 30000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-content {
  flex: 1;
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

.refresh-btn-native {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border: none;
  color: white;
  padding: 12px 24px;
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
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.refresh-btn-native:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn-native .btn-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-glow);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
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

.stat-icon :deep(svg) {
  width: 32px;
  height: 32px;
}

.stat-icon.blue {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-icon.purple {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.stat-icon.red {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.stat-icon.orange {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
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
  /* 移除了左侧边框 */
}

.risk-card.low {
}

.risk-card.medium {
}

.risk-card.high {
}

.risk-card.critical {
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

/* 趋势指示器 */
.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.stat-trend :deep(svg) {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.stat-trend.up {
  color: var(--accent-success);
}

.stat-trend.down {
  color: var(--accent-danger);
}

.stat-trend.secondary {
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 4px;
}

.stat-alert {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--accent-danger);
  font-weight: 500;
}

.stat-alert :deep(svg) {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.stat-progress {
  margin-top: 8px;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.dashboard-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 32px;
}


.network-graph-card {
  height: 400px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .page-title {
    font-size: 24px;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-title {
    font-size: 20px;
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
  
  .alerts-section {
    padding: 16px;
  }
  
  .alert-item {
    padding: 12px;
    gap: 12px;
  }
  
  .alert-icon {
    width: 36px;
    height: 36px;
  }
}
</style>
