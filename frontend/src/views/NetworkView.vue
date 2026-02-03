<template>
  <div class="network">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.monitored_posts || 0 }}</div>
        <div class="stat-label">{{ $t('network.monitoredPosts') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.monitored_agents || 0 }}</div>
        <div class="stat-label">{{ $t('network.monitoredAgents') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.processed_connections || 0 }}</div>
        <div class="stat-label">{{ $t('network.processedConnections') }}</div>
      </div>
    </div>

    <!-- 网络图 -->
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <el-icon><Share /></el-icon>
          <span>{{ $t('network.chartTitle') }}</span>
        </div>
      </div>
      <div ref="networkContainer" class="network-container"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Share, Refresh, Loading } from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import { useLanguageStore } from '@/stores/language'
import { storeToRefs } from 'pinia'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'

const languageStore = useLanguageStore()
const store = useDataStore()
const { networkData, isLoading } = storeToRefs(store)

const networkContainer = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let refreshInterval: number | undefined

const stats = ref({
  monitored_posts: 0,
  monitored_agents: 0,
  processed_connections: 0
})

/**
 * 监听语言变化，重新渲染图表
 */
watch(() => languageStore.locale, () => {
  nextTick(() => {
    initNetworkChart()
  })
})

/**
 * 初始化网络图并计算展示数据
 */
const initNetworkChart = () => {
  if (!networkContainer.value) return
  if (chart) {
    chart.dispose()
    chart = null
  }
  
  chart = echarts.init(networkContainer.value)
  
  const data = networkData.value
  const nodes = Array.isArray(data?.nodes) ? data.nodes : []
  const edges = Array.isArray(data?.edges) ? data.edges : []
  
  renderChart({ nodes, edges })
}

/**
 * 渲染网络图
 */
const renderChart = (data: any) => {
  if (!chart) return
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      borderColor: 'rgba(75, 85, 99, 0.4)',
      textStyle: { color: '#f9fafb' }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: data.nodes.map((node: any) => {
        const value = node.value ?? node.post_count ?? 1
        const group = node.group ?? node.community ?? 0
        return {
          ...node,
          name: node.label || node.name || node.id,
          symbolSize: Math.sqrt(value || 1) * 6 + 18,
          itemStyle: {
            color: getNodeColor(group)
          }
        }
      }),
      links: data.edges.map((edge: any) => {
        const weight = edge.value ?? edge.weight ?? 1
        return {
          source: edge.source || edge.from,
          target: edge.target || edge.to,
          value: weight,
          lineStyle: {
            width: Math.max(1, weight / 2),
            curveness: 0.2,
            color: weight >= 8 ? '#ef4444' : '#6b7280'
          }
        }
      }),
      roam: true,
      label: {
        show: true,
        position: 'right',
        color: '#f9fafb'
      },
      emphasis: {
        focus: 'adjacency'
      },
      force: {
        repulsion: 300,
        edgeLength: 120
      }
    }]
  }
  
  chart.setOption(option)
}

/**
 * 获取节点颜色
 */
const getNodeColor = (group: number) => {
  const palette = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#eab308']
  const index = Math.abs(Number(group || 0)) % palette.length
  return palette[index]
}

/**
 * 拉取网络统计数据
 */
const fetchNetworkStats = async () => {
  try {
    const res = await dashboardApi.getDashboard()
    const data = res.data || {}
    stats.value = {
      monitored_posts: data.total_posts || 0,
      monitored_agents: data.total_agents || 0,
      processed_connections: data.total_connections || 0
    }
  } catch (error) {
    console.error('Failed to fetch network stats:', error)
    stats.value = {
      monitored_posts: 0,
      monitored_agents: 0,
      processed_connections: 0
    }
  }
}

/**
 * 刷新网络数据
 */
const refreshNetwork = async () => {
  await Promise.all([store.fetchNetwork(), fetchNetworkStats()])
  nextTick(() => {
    initNetworkChart()
  })
}

const resizeHandler = () => {
  chart?.resize()
}

onMounted(() => {
  refreshNetwork()
  refreshInterval = window.setInterval(refreshNetwork, 30000)
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
})
</script>

<style scoped>
.network {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.8), rgba(17, 24, 39, 0.9));
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: all 0.2s ease;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.25);
}

.stat-card:hover {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 16px 30px rgba(59, 130, 246, 0.18);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.chart-card {
  background: linear-gradient(160deg, rgba(15, 23, 42, 0.9), rgba(31, 41, 55, 0.8));
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 16px 36px rgba(15, 23, 42, 0.3);
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

.network-container {
  width: 100%;
  height: 700px;
  min-height: 500px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(59, 130, 246, 0.15);
}

/* 响应式 */
@media (max-width: 1024px) {
  .page-title {
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .network-container {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
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
  
  .network-container {
    height: 350px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 18px;
  }
  
  .title-icon {
    width: 24px;
    height: 24px;
  }
  
  .title-icon :deep(svg) {
    width: 24px;
    height: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .network-container {
    height: 300px;
  }
}
</style>
