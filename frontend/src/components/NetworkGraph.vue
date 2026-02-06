<template>
  <div ref="cardRef" class="network-graph-card">
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
        <span v-if="selectedAgent" class="selected-hint">
          已选中：{{ selectedAgent.name || selectedAgent.id }}
        </span>
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
    <div class="graph-body">
      <div class="graph-panel">
        <div ref="graphRef" class="graph-container"></div>

        <div v-if="loading" class="graph-loading">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>{{ $t('common.loading') }}</span>
        </div>

        <div v-if="!loading && (!graphData?.nodes || graphData.nodes.length === 0)" class="empty-state">
          <el-icon size="48"><Warning /></el-icon>
          <p>{{ $t('common.empty') }}</p>
        </div>
      </div>
    </div>

    <AgentDetail v-model:visible="detailDialogVisible" :agent="selectedAgent" :loading="detailLoading" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection, User, Link, Warning, RefreshRight, Loading } from '@element-plus/icons-vue'
import { dashboardApi, agentsApi } from '@/api'
import AgentDetail from '@/components/AgentDetail.vue'

const cardRef = ref<HTMLElement>()
const graphRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let lastNodeClickAt = 0

const loading = ref(true)
const graphData = ref<{
  nodes: any[]
  edges: any[]
  stats: { total_agents: number; total_interactions: number }
} | null>(null)
const selectedAgent = ref<any>(null)
const detailLoading = ref(false)
const detailDialogVisible = ref(false)

const selectNodeById = (nodeId: string, fallbackNode?: any) => {
  console.log('[NetworkGraph] selectNodeById called:', nodeId, fallbackNode)
  if (!nodeId) return
  selectedAgent.value = fallbackNode || selectedAgent.value
  detailDialogVisible.value = true
  console.log('[NetworkGraph] detailDialogVisible:', detailDialogVisible.value)
  lastNodeClickAt = Date.now()
  loadAgentDetail(nodeId)
}

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
      triggerOn: 'mousemove',
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
              互动影响力: <span style="color:#a855f7">${(params.data.pagerank_score * 100).toFixed(2)}%</span>
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
          show: node.symbolSize > 25,
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
        repulsion: 150,
        edgeLength: 100,
        gravity: 0.05,
        layoutAnimation: true
      },
      progressiveThreshold: 500,
      progressive: 100,
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      blur: {
        itemStyle: {
          opacity: 0.12
        },
        label: {
          opacity: 0.1
        },
        lineStyle: {
          opacity: 0.08
        }
      }
    }]
  }
  
  chart.setOption(option)

  const handleEchartsEvent = (params: any) => {
    console.log('[NetworkGraph] Chart click event:', params.dataType, params.data)
    const isNode = params?.dataType === 'node'
    const nodeId = params?.data?.id || params?.data?.agent_id || params?.data?.agentId
    console.log('[NetworkGraph] isNode:', isNode, 'nodeId:', nodeId)
    if (isNode && nodeId) {
      selectNodeById(String(nodeId), params.data)
    }
  }

  chart.off('click')
  chart.off('mousedown')
  chart.on('click', handleEchartsEvent)
  chart.on('mousedown', handleEchartsEvent)

  const handleZrEvent = (event: any) => {
    if (!event?.target) {
      if (Date.now() - lastNodeClickAt > 200) {
        clearSelection()
      }
    }
  }

  chart.getZr().off('click')
  chart.getZr().on('click', handleZrEvent)
}

const resetZoom = () => {
  if (chart) {
    chart.dispatchAction({
      type: 'restore'
    })
  }
}

const clearSelection = () => {
  detailDialogVisible.value = false
  selectedAgent.value = null
}

const loadAgentDetail = async (agentId: string) => {
  detailLoading.value = true
  try {
    const res = await agentsApi.getAgent(agentId)
    selectedAgent.value = res.data || null
  } catch (error) {
    console.error('Failed to fetch agent detail:', error)
    // 保留节点的 fallback 数据，避免弹框空白
  } finally {
    detailLoading.value = false
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

const handleDocumentClick = (event: MouseEvent) => {
  if (detailDialogVisible.value) return
  const target = event.target as Node | null
  if (cardRef.value && target && !cardRef.value.contains(target)) {
    clearSelection()
  }
}

watch(() => graphData.value, () => {
  nextTick(() => {
    initChart()
  })
}, { deep: true })

watch(detailDialogVisible, (visible) => {
  if (!visible) {
    selectedAgent.value = null
  }
})

onMounted(() => {
  fetchData()
  window.addEventListener('resize', resizeHandler)
  window.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  window.removeEventListener('click', handleDocumentClick)
  chart?.dispose()
})
</script>

<style scoped>
.network-graph-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 640px;
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

.selected-hint {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.graph-body {
  display: flex;
  gap: 16px;
  min-height: 560px;
  flex: 1;
}

.graph-panel {
  flex: 2;
  min-width: 0;
  position: relative;
  height: 100%;
}

.detail-panel {
  flex: 1;
  min-width: 320px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.detail-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.clear-btn {
  font-size: 12px;
}

.graph-container {
  width: 100%;
  height: 100%;
  min-height: 560px;
}

.graph-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 14px;
  background: rgba(10, 15, 28, 0.35);
  border-radius: 12px;
  pointer-events: none;
}

.loading-icon {
  font-size: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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

@media (max-width: 1200px) {
  .graph-body {
    flex-direction: column;
  }

  .detail-panel {
    min-width: 0;
    min-height: 320px;
  }
}
</style>
