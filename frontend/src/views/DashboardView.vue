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
            <span class="stat-label">当前风险等级</span>
            <span class="stat-value">{{ getRiskLabel(stats?.risk_level) }}</span>
          </div>
        </div>
        <div class="risk-indicator-bar">
          <div class="risk-level" :style="{ width: getRiskPercentage(stats?.risk_level) + '%' }"></div>
        </div>
      </div>

      <!-- 24小时帖子数 -->
      <div class="stat-card">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon blue">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">24小时帖子数</span>
            <span class="stat-value">{{ formatNumber(stats?.total_posts) }}</span>
          </div>
        </div>
        <div class="stat-trend up">
          <el-icon><ArrowUp /></el-icon>
          <span>+12.5%</span>
        </div>
      </div>

      <!-- 活跃 Agent -->
      <div class="stat-card">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon purple">
            <el-icon size="32"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">活跃 Agent</span>
            <span class="stat-value">{{ formatNumber(stats?.active_agents) }}</span>
          </div>
        </div>
        <div class="stat-trend">
          <span>实时监控中</span>
        </div>
      </div>

      <!-- 高风险帖子 -->
      <div class="stat-card danger-card">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon red">
            <el-icon size="32"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">高风险帖子</span>
            <span class="stat-value">{{ formatNumber(stats?.danger_count) }}</span>
          </div>
        </div>
        <div class="stat-alert" v-if="stats?.danger_count > 0">
          <el-icon><Warning /></el-icon>
          <span>需要关注</span>
        </div>
      </div>

      <!-- 平均阴谋指数 -->
      <div class="stat-card">
        <div class="card-glow"></div>
        <div class="card-content">
          <div class="stat-icon orange">
            <el-icon size="32"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-label">平均阴谋指数</span>
            <span class="stat-value">{{ stats?.avg_risk }}/10</span>
          </div>
        </div>
        <el-progress 
          :percentage="(stats?.avg_risk || 0) * 10" 
          :color="getProgressColor(stats?.avg_risk || 0)"
          :show-text="false"
          class="stat-progress"
        />
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 趋势图 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            <span>7天阴谋指数趋势</span>
          </div>
          <el-radio-group v-model="trendPeriod" size="small">
            <el-radio-button label="7d">7天</el-radio-button>
            <el-radio-button label="30d">30天</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>

      <!-- 风险分布 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><PieChart /></el-icon>
            <span>风险等级分布</span>
          </div>
        </div>
        <div ref="pieChartRef" class="chart-container"></div>
      </div>
    </div>

    <!-- 最近警报 -->
    <div class="alerts-section" v-if="recentAlerts.length > 0">
      <div class="section-header">
        <h3>
          <el-icon><Bell /></el-icon>
          最近警报
        </h3>
        <el-button link type="primary">查看全部</el-button>
      </div>
      <div class="alerts-list">
        <div 
          v-for="alert in recentAlerts" 
          :key="alert.id" 
          class="alert-item"
          :class="alert.level"
        >
          <div class="alert-icon">
            <el-icon size="20"><Warning /></el-icon>
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-desc">{{ alert.description }}</div>
            <div class="alert-time">{{ alert.time }}</div>
          </div>
          <el-button link type="primary" size="small">处理</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { useDataStore } from '@/stores/data'
import { storeToRefs } from 'pinia'
import { 
  DataLine, 
  Refresh, 
  Warning, 
  Document, 
  UserFilled, 
  Bell,
  TrendCharts,
  PieChart,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import { dashboardApi } from '@/api'

const store = useDataStore()
const { stats, trend, isLoading } = storeToRefs(store)

const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

const trendPeriod = ref('7d')
const riskDistribution = ref<Record<string, number>>({
  low: 0,
  medium: 0,
  high: 0,
  critical: 0
})

// 定义趋势数据类型
interface TrendItem {
  date: string
  count: number
}

// 模拟最近警报数据
const recentAlerts = ref([
  {
    id: 1,
    level: 'high',
    title: '检测到高风险帖子',
    description: 'Agent "suspicious_user_01" 发布了包含敏感关键词的内容',
    time: '5分钟前'
  },
  {
    id: 2,
    level: 'medium',
    title: '异常活动模式',
    description: '多个 Agent 在短时间内频繁互动',
    time: '15分钟前'
  },
  {
    id: 3,
    level: 'low',
    title: '新 Agent 注册',
    description: '发现新的 Agent 加入监控范围',
    time: '1小时前'
  }
])

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

// 获取风险标签
const getRiskLabel = (level: string) => {
  const labels: Record<string, string> = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险',
    'critical': '极高风险'
  }
  return labels[level] || level
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
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      borderColor: 'rgba(75, 85, 99, 0.4)',
      textStyle: { color: '#f9fafb' },
      formatter: (params: any) => {
        return `<div style="font-weight:600">${params[0].name}</div>
                <div>高风险帖子: <span style="color:#ef4444;font-weight:600">${params[0].value}</span></div>`
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
      data: (trend.value as TrendItem[]).map((t: TrendItem) => t.date),
      axisLine: { lineStyle: { color: 'rgba(75, 85, 99, 0.4)' } },
      axisLabel: { color: '#9ca3af' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(75, 85, 99, 0.2)' } },
      axisLabel: { color: '#9ca3af' }
    },
    series: [{
      data: (trend.value as TrendItem[]).map((t: TrendItem) => t.count),
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
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#06b6d4' }
          ]
        }
      },
      itemStyle: {
        color: '#3b82f6',
        borderWidth: 2,
        borderColor: '#0a0f1c'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.02)' }
          ]
        }
      }
    }]
  }
  
  trendChart.setOption(option)
}

// 初始化饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  
  pieChart = echarts.init(pieChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      borderColor: 'rgba(75, 85, 99, 0.4)',
      textStyle: { color: '#f9fafb' }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#9ca3af' }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#0a0f1c',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          color: '#f9fafb'
        }
      },
      data: [
        { value: riskDistribution.value.low, name: '低风险', itemStyle: { color: '#10b981' } },
        { value: riskDistribution.value.medium, name: '中风险', itemStyle: { color: '#f59e0b' } },
        { value: riskDistribution.value.high, name: '高风险', itemStyle: { color: '#ef4444' } },
        { value: riskDistribution.value.critical, name: '极高风险', itemStyle: { color: '#7c3aed' } }
      ]
    }]
  }
  
  pieChart.setOption(option)
}

// 获取风险分布数据
const fetchRiskDistribution = async () => {
  try {
    const res = await dashboardApi.getRiskDistribution()
    riskDistribution.value = res.data || { low: 0, medium: 0, high: 0, critical: 0 }
    nextTick(() => {
      initPieChart()
    })
  } catch (error) {
    console.error('Failed to fetch risk distribution:', error)
  }
}

// 刷新数据
const refreshData = async () => {
  await store.fetchDashboard()
  await fetchRiskDistribution()
  nextTick(() => {
    initTrendChart()
  })
}

// 自动刷新
let refreshInterval: number
const resizeHandler = () => {
  trendChart?.resize()
  pieChart?.resize()
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
  pieChart?.dispose()
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
  background: rgba(239, 68, 68, 0.1);
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
  grid-template-columns: 2fr 1fr;
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

.chart-container {
  height: 300px;
}

/* 警报区域 */
.alerts-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-header h3 :deep(svg) {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(17, 24, 39, 0.5);
  border-radius: 12px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
}

.alert-item:hover {
  background: rgba(17, 24, 39, 0.8);
}

.alert-item.high {
  border-left-color: #ef4444;
}

.alert-item.medium {
  border-left-color: #f59e0b;
}

.alert-item.low {
  border-left-color: #10b981;
}

.alert-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  flex-shrink: 0;
}

.alert-icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.alert-time {
  font-size: 12px;
  color: var(--text-muted);
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}

@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
  
  .page-title {
    font-size: 24px;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
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
