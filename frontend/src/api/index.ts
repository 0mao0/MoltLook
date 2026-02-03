/**
 * API 客户端
 */
import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Dashboard API
export const dashboardApi = {
  getDashboard: (days?: number) => api.get('/dashboard/stats', { params: days ? { days } : undefined }),
  getRealtimeStats: () => api.get('/stats/realtime'),
  getRiskDistribution: () => api.get('/dashboard/risk-distribution')
}

// Feed API
export const feedApi = {
  getFeed: (params?: { page?: number; pageSize?: number; min_score?: number; submolt?: string; risk_level?: string }) =>
    api.get('/feed', { params }),
  getPost: (id: string) => api.get(`/posts/${id}`),
  getComments: (id: string) => api.get(`/posts/${id}/comments`)
}

// Network API
export const networkApi = {
  getNetwork: (params?: { limit?: number; community_id?: number }) =>
    api.get('/network', { params }),
  getCommunities: () => api.get('/network/communities'),
  getAgentConnections: (agentId: string, limit?: number) =>
    api.get(`/network/agent/${agentId}/connections`, { params: { limit } })
}

// Agents API
export const agentsApi = {
  getAgents: (params?: { page?: number; page_size?: number; risk_level?: string; community_id?: number }) =>
    api.get('/agents', { params }),
  getAgent: (id: string) => api.get(`/agent/${id}`),
  getRiskyAgents: (params?: { limit?: number; min_conspiracy?: number }) =>
    api.get('/agents/risky', { params }),
  getAgentStats: () => api.get('/agents/stats'),
  searchAgents: (query: string, limit?: number) =>
    api.get('/agents/search', { params: { query, limit } })
}

// Translation & Analysis API
export const translationApi = {
  translate: (content: string) => api.post('/translate', { content }, { timeout: 30000 }),
  analyze: (content: string, riskLevel: string, targetLang: string) => 
    api.post('/analyze', { content, risk_level: riskLevel, target_lang: targetLang }, { timeout: 45000 })
}

export default api
