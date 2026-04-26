import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'

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
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    } else if (error.response?.status === 403) {
      ElMessage.error('账号已被禁用，请联系管理员')
      const userStore = useUserStore()
      userStore.logout()
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

  // 流式对话
  chatStream: (data, callbacks = {}) => {
    const { onChunk, onFinish, onError } = callbacks
    const token = localStorage.getItem('token')

    // 代理被缓冲了，直接请求后端
    const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8000/chat/stream'
      : '/api/chat/stream'

    return new Promise((resolve, reject) => {
      fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      }).then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        const read = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              if (buffer && onFinish) {
                try {
                  const lines = buffer.split('\n')
                  for (const line of lines) {
                    if (line.startsWith('data: ')) {
                      const jsonStr = line.slice(6)
                      if (jsonStr.trim()) {
                        const data = JSON.parse(jsonStr)
                        if (data.type === 'finish' && onFinish) {
                          onFinish(data)
                        } else if (data.type === 'error' && onError) {
                          onError(data.error)
                        }
                      }
                    }
                  }
                } catch (e) {
                  // 忽略解析错误
                }
              }
              resolve({ cancelled: false })
              return
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop()

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(6)
                  if (jsonStr.trim()) {
                    const data = JSON.parse(jsonStr)
                    if (data.content && onChunk) {
                      onChunk(data.content)
                    } else if (data.type === 'finish' && onFinish) {
                      onFinish(data)
                    } else if (data.type === 'error' && onError) {
                      onError(data.error)
                    }
                  }
                } catch (e) {
                  // 忽略解析错误
                }
              }
            }

            if (!done) {
              read()
            }
          }).catch(error => {
            if (onError) {
              onError(error.message || '读取流失败')
            }
            reject(error)
          })
        }

        read()
      }).catch(error => {
        if (onError) {
          onError(error.message || '请求失败')
        }
        reject(error)
      })
    })
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

  // 知识库管理
  getKnowledgeFiles: () => {
    return request.get('/knowledge/files')
  },

  deleteKnowledgeFile: (filename) => {
    return request.delete(`/knowledge/files/${filename}`)
  },

  getKnowledgeFileChunks: (filename) => {
    return request.get(`/knowledge/files/${filename}/chunks`)
  },

  searchKnowledgePreview: (query, agentType, topK = 5) => {
    return request.get('/knowledge/search_preview', { params: { query, agent_type: agentType, top_k: topK } })
  },

  getKnowledgeStats: (agentType) => {
    return request.get('/knowledge/stats', { params: { agent_type: agentType } })
  },

  saveReferenceDocument: (docId, source, agentType = 'tax_basic') => {
    return request.post('/knowledge/save-reference', null, { params: { doc_id: docId, source, agent_type: agentType } })
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
  },

  // ===== 支付相关 =====
  createPaymentOrder: (data) => {
    return request.post('/payment/create', data)
  },

  queryPaymentStatus: (orderId) => {
    return request.get(`/payment/status/${orderId}`)
  },

  closePaymentOrder: (orderId) => {
    return request.post(`/payment/close/${orderId}`)
  }
}

export default api
