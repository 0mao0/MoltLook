<template>
  <div class="dashboard">
    <div class="stats-grid">
      <!-- 风险等级卡片 -->
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

      <!-- 活跃 Agent -->
      <div class="stat-card" style="cursor: pointer" @click="router.push('/agents')">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon purple">
            <el-icon size="32"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.activeAgents') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.active_agents) }}</span>
          </div>
        </div>
        <div class="stat-trend">
          <span>{{ $t('dashboard.monitoring') }}</span>
        </div>
      </div>

      <!-- 高危帖子（合并24小时帖子数和高风险帖子） -->
      <div class="stat-card danger-card" style="cursor: pointer" @click="router.push({ path: '/feed', query: { risk: 'high' } })">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon red">
            <el-icon size="32" color="#ef4444"><WarningFilled /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.highRiskPosts') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.danger_count) }}</span>
          </div>
        </div>
        <div class="stat-trend secondary">
          <el-icon size="14"><Document /></el-icon>
          <span>{{ $t('dashboard.monitoredPosts', { count: formatNumber(stats?.posts_24h) }) }}</span>
        </div>
      </div>

      <!-- 总计帖子数 -->
      <div class="stat-card" style="cursor: pointer" @click="router.push('/feed')">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon blue">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ $t('dashboard.totalPosts') }}</span>
            <span class="stat-value">{{ formatNumber(stats?.posts_24h) }}</span>
          </div>
        </div>
        <div class="stat-trend" :class="getGrowthClass(stats?.growth_rate)">
          <el-icon v-if="stats?.growth_rate > 0"><ArrowUp /></el-icon>
          <el-icon v-else-if="stats?.growth_rate < 0"><ArrowDown /></el-icon>
          <span>{{ formatGrowthRate(stats?.growth_rate) }}</span>
        </div>
      </div>
    </div>

    <div class="dashboard-charts">
      <!-- 关系图 -->
      <div class="chart-card">
        <NetworkGraph />
      </div>
      
      <!-- 趋势图 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            <span>{{ $t('dashboard.trendTitle') }}</span>
          </div>
          <el-radio-group v-model="trendPeriod" size="small">
            <el-radio-button label="7d">{{ $t('dashboard.period7d') }}</el-radio-button>
            <el-radio-button label="30d">{{ $t('dashboard.period30d') }}</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import NetworkGraph from '@/components/NetworkGraph.vue'
import { 
  DataLine, 
  Refresh, 
  Warning, 
  WarningFilled,
  Document, 
  UserFilled,
  TrendCharts,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import { dashboardApi } from '@/api'
import { riskLabels } from '@/locales'

const router = useRouter()
const { t } = useI18n()
const languageStore = useLanguageStore()
const store = useDataStore()
const { stats, trend, isLoading } = storeToRefs(store)

const trendChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const trendPeriod = ref('7d')

// 定义趋势数据类型
interface TrendItem {
  date: string
  total_count: number
  risk_score_sum: number
  risk_index: number
}

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

// 获取进度条颜色
const getProgressColor = (score: number) => {
  if (score >= 8) return '#ef4444'
  if (score >= 5) return '#f59e0b'
  return '#10b981'
}

// 初始化趋势图
const initTrendChart = () => {
  if (!trendChartRef.value) {
    console.warn('trendChartRef is null')
    return
  }
  
  if (trendChart) {
    trendChart.dispose()
  }
  trendChart = echarts.init(trendChartRef.value)
  
  const trendData = (trend.value as TrendItem[])
  console.log('Trend data:', trendData)
  
  if (!trendData || trendData.length === 0) {
    console.warn('Trend data is empty')
    trendChart.clear()
    return
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      borderColor: 'rgba(75, 85, 99, 0.4)',
      textStyle: { color: '#f9fafb' },
      formatter: (params: any) => {
        const data = params[0]
        const trendItem = trendData[data.dataIndex]
        return `<div style="font-weight:600">${data.name}</div>
                <div>当日风险指数: <span style="color:#ef4444;font-weight:600">${trendItem.risk_index}</span></div>
                <div>风险分数总和: ${trendItem.risk_score_sum}</div>
                <div>当日总帖子数: ${trendItem.total_count}</div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trendData.map((t: any) => t.date),
      axisLine: { lineStyle: { color: 'rgba(75, 85, 99, 0.4)' } },
      axisLabel: { color: '#9ca3af' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(75, 85, 99, 0.2)' } },
      axisLabel: { 
        color: '#9ca3af'
      }
    },
    series: [{
      name: '当日风险指数',
      data: trendData.map((t: any) => t.risk_index),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#ef4444' },
            { offset: 1, color: '#f97316' }
          ]
        }
      },
      itemStyle: {
        color: '#ef4444',
        borderWidth: 2,
        borderColor: '#0a0f1c'
      },
      areaStyle: {
        color: {
          type: 'linear', 
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.02)' }
          ]
        }
      }
    }]
  }
  
  trendChart.setOption(option)
}

// 监听语言变化
watch(() => languageStore.locale, () => {
  nextTick(() => {
    initTrendChart()
  })
})

/**
 * 刷新数据
 */
const refreshData = async () => {
  const days = trendPeriod.value === '30d' ? 30 : 7
  await store.fetchDashboard()
  nextTick(() => {
    initTrendChart()
  })
}

// 监听时间周期变化
watch(trendPeriod, async () => {
  const days = trendPeriod.value === '30d' ? 30 : 7
  try {
    const res = await dashboardApi.getDashboard(days)
    if (res.data && res.data.trend) {
      trend.value = res.data.trend
    }
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
  }
  nextTick(() => {
    initTrendChart()
  })
})

// 监听趋势数据变化
watch(trend, () => {
  nextTick(() => {
    initTrendChart()
  })
}, { deep: true })

// 自动刷新
let refreshInterval: number
const resizeHandler = () => {
  trendChart?.resize()
}

onMounted(() => {
  refreshData()
  refreshInterval = window.setInterval(refreshData, 30000)
  
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
  window.removeEventListener('resize', resizeHandler)
  trendChart?.dispose()
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
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-title :deep(svg) {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 自定义时间选择器样式 */
.chart-header :deep(.el-radio-group) {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 4px;
  border: 1px solid var(--border-color);
}

.chart-header :deep(.el-radio-button) {
  margin: 0;
}

.chart-header :deep(.el-radio-button__inner) {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  padding: 6px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
  box-shadow: none;
}

.chart-header :deep(.el-radio-button__inner:hover) {
  color: var(--text-primary);
  background: rgba(59, 130, 246, 0.1);
}

.chart-header :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.chart-header :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.chart-container {
  height: 300px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-charts {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .dashboard-charts {
    grid-template-columns: 1fr;
  }
  
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
  
  .chart-card {
    padding: 16px;
  }
  
  .chart-container {
    height: 250px;
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
