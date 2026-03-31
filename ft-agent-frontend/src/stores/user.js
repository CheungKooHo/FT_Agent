import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!userInfo.value && !!token.value)

  // 登录
  async function login(username, password) {
    try {
      const response = await api.login(username, password)
      if (response.status === 'success') {
        userInfo.value = response.data
        // 使用 JWT token
        token.value = response.data.access_token
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('userInfo', JSON.stringify(response.data))
        return { success: true }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 注册
  async function register(userData) {
    try {
      const response = await api.register(userData)
      if (response.status === 'success') {
        userInfo.value = response.data
        // 使用 JWT token
        token.value = response.data.access_token
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('userInfo', JSON.stringify(response.data))
        return { success: true, freeTokenGranted: response.data.free_token_granted }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 登出
  function logout() {
    userInfo.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  // 从本地存储恢复用户信息
  function restoreUserInfo() {
    const savedUserInfo = localStorage.getItem('userInfo')
    if (savedUserInfo) {
      try {
        userInfo.value = JSON.parse(savedUserInfo)
      } catch (e) {
        console.error('Failed to parse user info:', e)
      }
    }
  }

  // 更新用户信息
  async function updateUserInfo(data) {
    try {
      const response = await api.updateUserInfo(userInfo.value.user_id, data)
      if (response.status === 'success') {
        userInfo.value = { ...userInfo.value, ...response.data }
        localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
        return { success: true }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 初始化时恢复用户信息
  restoreUserInfo()

  return {
    userInfo,
    token,
    isLoggedIn,
    login,
    register,
    logout,
    updateUserInfo
  }
})
