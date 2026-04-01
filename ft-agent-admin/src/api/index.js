import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 请求拦截器 - 添加 admin token
request.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('admin_token')
      localStorage.removeItem('adminInfo')
      window.location.href = '/login'
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

const api = {
  // Admin 登录
  adminLogin: (username, password) => {
    return request.post('/admin/login', { username, password })
  },

  // 概览统计
  getOverview: () => {
    return request.get('/admin/stats/overview')
  },

  // 用户管理
  getUsers: (page = 1, pageSize = 20, filters = {}) => {
    const params = { page, page_size: pageSize, ...filters }
    return request.get('/admin/users', { params })
  },

  toggleUserStatus: (userId) => {
    return request.put(`/admin/users/${userId}/toggle-status`)
  },

  grantToken: (userId, amount) => {
    return request.post(`/admin/users/${userId}/grant-token`, null, { params: { amount } })
  },

  // Token 统计
  getTokenStats: () => {
    return request.get('/admin/stats/token-usage')
  },

  // 政策文档
  getPolicyDocuments: (page = 1, pageSize = 20, category = null) => {
    const params = { page, page_size: pageSize }
    if (category) params.category = category
    return request.get('/admin/policy-documents', { params })
  },

  createPolicyDocument: (data) => {
    return request.post('/admin/policy-documents', null, { params: data })
  },

  updatePolicyDocument: (docId, data) => {
    return request.put(`/admin/policy-documents/${docId}`, null, { params: data })
  },

  deletePolicyDocument: (docId) => {
    return request.delete(`/admin/policy-documents/${docId}`)
  },

  // 系统配置
  getSystemConfigs: () => {
    return request.get('/admin/system-configs')
  },

  updateSystemConfig: (key, value) => {
    return request.put(`/admin/system-configs/${key}`, null, { params: { value } })
  },

  // Agent 配置管理
  getAgents: () => {
    return request.get('/admin/agents')
  },

  createAgent: (data) => {
    return request.post('/admin/agents', null, { params: data })
  },

  updateAgent: (agentId, data) => {
    return request.put(`/admin/agents/${agentId}`, null, { params: data })
  },

  deleteAgent: (agentId) => {
    return request.delete(`/admin/agents/${agentId}`)
  },

  // 订阅版本管理
  getTiers: () => {
    return request.get('/admin/tiers')
  },

  createTier: (data) => {
    return request.post('/admin/tiers', null, { params: data })
  },

  updateTier: (tierId, data) => {
    return request.put(`/admin/tiers/${tierId}`, null, { params: data })
  },

  deleteTier: (tierId) => {
    return request.delete(`/admin/tiers/${tierId}`)
  },

  // 知识库管理
  getKnowledgeFiles: (page = 1, pageSize = 20, agentType = null) => {
    const params = { page, page_size: pageSize }
    if (agentType) params.agent_type = agentType
    return request.get('/admin/knowledge/files', { params })
  },

  uploadKnowledgeFile: (formData) => {
    return request.post('/admin/knowledge/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  deleteKnowledgeFile: (filename) => {
    return request.delete(`/admin/knowledge/files/${filename}`)
  },

  getKnowledgeStats: () => {
    return request.get('/admin/knowledge/stats')
  }
}

export default api
