/**
 * Pinia 数据存储
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dashboardApi, feedApi, networkApi, agentsApi } from '@/api'

export const useDataStore = defineStore('data', () => {
  // State
  const dashboard = ref<any>(null)
  const posts = ref<any[]>([])
  const feedTotal = ref(0)
  const network = ref<any>({ nodes: [], edges: [] })
  const agents = ref<any[]>([])
  const loading = ref(false)
  const lastUpdate = ref(0)
  const trend = ref<any[]>([])

  // Getters
  // 后端 /api/dashboard/stats 直接返回 stats 对象，不是嵌套结构
  const stats = computed(() => dashboard.value || null)
  const networkData = computed(() => network.value || { nodes: [], edges: [] })
  const isLoading = computed(() => loading.value)

  // Actions
  async function fetchDashboard() {
    loading.value = true
    try {
      const res = await dashboardApi.getDashboard()
      dashboard.value = res.data
      if (res.data && res.data.trend) {
        trend.value = res.data.trend
      }
      lastUpdate.value = Date.now()
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchFeed(params?: { 
    page?: number; 
    pageSize?: number;
    riskLevel?: string;
    submolt?: string;
    limit?: number; 
    min_score?: number 
  }) {
    loading.value = true
    try {
      const requestParams: any = {
        page: params?.page,
        pageSize: params?.pageSize,
        min_score: params?.min_score
      }
      
      if (params?.riskLevel && params.riskLevel.trim()) {
        requestParams.risk_level = params.riskLevel
      }
      
      if (params?.submolt && params.submolt.trim()) {
        requestParams.submolt = params.submolt
      }
      
      const res = await feedApi.getFeed(requestParams)
      const data = res.data
      posts.value = data?.items || []
      feedTotal.value = data?.total || 0
      
      if (agents.value.length === 0) {
        await fetchAgents()
      }
    } catch (error) {
      console.error('Failed to fetch feed:', error)
      posts.value = []
      feedTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  async function fetchNetwork(params?: { limit?: number; community_id?: number }) {
    loading.value = true
    try {
      const res = await networkApi.getNetwork(params)
      network.value = res.data || { nodes: [], edges: [] }
    } catch (error) {
      console.error('Failed to fetch network:', error)
      network.value = { nodes: [], edges: [] }
    } finally {
      loading.value = false
    }
  }

  async function fetchAgents(params?: { 
    page?: number;
    pageSize?: number;
    riskLevel?: string;
  }) {
    loading.value = true
    try {
      const res = await agentsApi.getAgents({
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        risk_level: params?.riskLevel
      })
      const data = res.data
      
      if (data && data.items && Array.isArray(data.items)) {
        agents.value = data.items.filter((item: any) => item && item.id)
      } else if (Array.isArray(data)) {
        agents.value = data.filter((item: any) => item && item.id)
      } else {
        agents.value = []
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
      agents.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    dashboard,
    posts,
    feedTotal,
    network,
    agents,
    loading,
    lastUpdate,
    stats,
    trend,
    networkData,
    isLoading,
    fetchDashboard,
    fetchFeed,
    fetchNetwork,
    fetchAgents
  }
})
