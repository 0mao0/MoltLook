<template>
  <div class="network-graph-card" v-loading="loading">
    <div class="graph-header">
      <div class="graph-title">
        <el-icon><Connection /></el-icon>
        <span>{{ $t('network.chartTitle') }}</span>
      </div>
      <div class="graph-header-right">
        <div class="graph-stats" v-if="graphData?.stats">
          <span class="stat-item">
            <el-icon><User /></el-icon>
            {{ graphData.stats.total_agents }}
          </span>
          <span class="stat-item">
            <el-icon><Link /></el-icon>
            {{ graphData.stats.total_interactions }}
          </span>
        </div>
        <el-button
          type="primary"
          size="small"
          :icon="RefreshRight"
          @click="resetZoom"
          class="reset-btn"
        >
          {{ $t('common.reset') || '重置' }}
        </el-button>
      </div>
    </div>
    <div ref="graphRef" class="graph-container"></div>
    <div v-if="!loading && (!graphData?.nodes || graphData.nodes.length === 0)" class="empty-state">
      <el-icon size="48"><Warning /></el-icon>
      <p>{{ $t('common.empty') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection, User, Link, Warning, RefreshRight } from '@element-plus/icons-vue'
import { dashboardApi } from '@/api'

const graphRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const loading = ref(true)
const graphData = ref<{
  nodes: any[]
  edges: any[]
  stats: { total_agents: number; total_interactions: number }
} | null>(null)

const initChart = () => {
  if (!graphRef.value || !graphData.value?.nodes?.length) return
  
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(graphRef.value)
  
  const option = {
    grid: {
      left: '0%',
      right: '0%',
      top: '0%',
      bottom: '0%',
      containLabel: true
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(17, 24, 39, 0.95)',
      borderColor: 'rgba(75, 85, 99, 0.4)',
      textStyle: { color: '#f9fafb' },
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const danger = params.data.danger_index || 0
          let dangerLevel = '低风险'
          if (danger >= 70) dangerLevel = '极高风险'
          else if (danger >= 50) dangerLevel = '高风险'
          else if (danger >= 25) dangerLevel = '中风险'
          
          return `
            <div style="font-weight:600;margin-bottom:8px">${params.data.name}</div>
            <div style="color:#9ca3af;font-size:12px;line-height:1.8">
              危险指数: <span style="color:${params.data.itemStyle?.color || '#22c55e'};font-weight:700;font-size:16px">${danger}</span> / 100<br/>
              危险等级: <span style="color:${params.data.itemStyle?.color || '#22c55e'}">${dangerLevel}</span><br/>
              阴谋指数: <span style="color:#ef4444">${params.data.conspiracy_score}</span><br/>
              互动次数: <span style="color:#3b82f6">${params.data.interactions || 0}</span><br/>
              PageRank: ${params.data.pagerank_score}
            </div>
          `
        } else if (params.dataType === 'edge') {
          return `
            <div style="font-weight:600">互动关系</div>
            <div style="color:#9ca3af;font-size:12px">
              互动次数: <span style="color:#3b82f6;font-weight:600">${params.data.value}</span>
            </div>
          `
        }
        return ''
      }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: graphData.value.nodes.map(node => ({
        ...node,
        symbolSize: node.symbolSize || 35,
        label: {
          show: node.symbolSize > 30,
          fontSize: 10,
          color: '#f9fafb'
        }
      })),
      links: graphData.value.edges,
      roam: true,
      label: {
        position: 'right',
        formatter: '{b}',
        fontSize: 10,
        color: '#9ca3af'
      },
      lineStyle: {
        color: 'source',
        curveness: 0.1,
        width: 1.5
      },
      force: {
        repulsion: 120,
        edgeLength: 80,
        gravity: 0.03
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      }
    }]
  }
  
  chart.setOption(option)
}

const resetZoom = () => {
  if (chart) {
    chart.dispatchAction({
      type: 'restore'
    })
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await dashboardApi.getNetworkGraph()
    graphData.value = res.data
    await nextTick()
    initChart()
  } catch (error) {
    console.error('Failed to fetch network graph data:', error)
  } finally {
    loading.value = false
  }
}

const resizeHandler = () => {
  chart?.resize()
}

watch(() => graphData.value, () => {
  nextTick(() => {
    initChart()
  })
}, { deep: true })

onMounted(() => {
  fetchData()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
})
</script>

<style scoped>
.network-graph-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.graph-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.graph-title :deep(svg) {
  width: 18px;
  height: 18px;
  color: var(--accent-primary);
}

.graph-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.graph-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: 6px;
}

.stat-item :deep(svg) {
  width: 12px;
  height: 12px;
}

.reset-btn {
  padding: 4px 12px;
  height: 24px;
  font-size: 12px;
}

.graph-container {
  flex: 1;
  min-height: 280px;
  width: 100%;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 12px;
}

.empty-state :deep(svg) {
  color: var(--text-muted);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}
</style>
