import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 60000  // 文件上传可能需要更长时间
})

// 请求拦截器 - 添加用户 token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      router.push('/login')
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API 接口
const api = {
  // 用户认证
  login: (username, password) => {
    return request.post('/login', { username, password })
  },

  register: (data) => {
    return request.post('/register', data)
  },

  getUserInfo: (userId) => {
    return request.get(`/user/${userId}`)
  },

  updateUserInfo: (userId, data) => {
    return request.put(`/user/${userId}`, data)
  },

  // 对话
  chat: (data) => {
    return request.post('/chat', data)
  },

  // 记忆管理
  saveMemory: (data) => {
    return request.post('/memory', data)
  },

  getUserMemories: (userId, memoryType = null) => {
    const params = memoryType ? { memory_type: memoryType } : {}
    return request.get(`/memory/${userId}`, { params })
  },

  deleteMemory: (userId, key, memoryType = 'fact') => {
    return request.delete('/memory', {
      params: { user_id: userId, key, memory_type: memoryType }
    })
  },

  // 对话历史
  getConversationHistory: (userId, params = {}) => {
    return request.get(`/conversation_history/${userId}`, { params })
  },

  clearConversationHistory: (userId, params = {}) => {
    return request.delete('/conversation_history', {
      params: { user_id: userId, ...params }
    })
  },

  // 文件上传
  uploadFile: (file, agentType, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)

    return request.post('/upload_file', formData, {
      params: { agent_type: agentType },
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
  },

  getUploadedFiles: () => {
    return request.get('/uploaded_files')
  },

  // ===== Token 相关 =====
  getTokenBalance: (userId) => {
    return request.get('/token/balance', { params: { user_id: userId } })
  },

  getTokenTransactions: (userId, limit = 50) => {
    return request.get('/token/transactions', { params: { user_id: userId, limit } })
  },

  rechargeToken: (userId, amount) => {
    return request.post('/token/recharge', null, { params: { user_id: userId, amount } })
  },

  getTokenPrice: () => {
    return request.get('/token/price')
  },

  // ===== 订阅相关 =====
  getSubscription: (userId) => {
    return request.get('/subscription', { params: { user_id: userId } })
  },

  upgradeSubscription: (userId, tierCode) => {
    return request.post('/subscription/upgrade', null, { params: { user_id: userId, tier_code: tierCode } })
  },

  getTiers: () => {
    return request.get('/tiers')
  }
}

export default api
