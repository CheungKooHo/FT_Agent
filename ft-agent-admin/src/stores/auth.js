import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const adminInfo = ref(null)
  const token = ref(localStorage.getItem('admin_token') || '')

  const isLoggedIn = computed(() => !!adminInfo.value && !!token.value)

  // 登录
  async function login(username, password) {
    try {
      const response = await api.adminLogin(username, password)
      if (response.status === 'success') {
        adminInfo.value = response.data
        token.value = response.data.access_token
        localStorage.setItem('admin_token', response.data.access_token)
        localStorage.setItem('adminInfo', JSON.stringify(response.data))
        return { success: true }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 登出
  function logout() {
    adminInfo.value = null
    token.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('adminInfo')
  }

  // 从本地存储恢复
  function restoreAuth() {
    const savedAdminInfo = localStorage.getItem('adminInfo')
    if (savedAdminInfo) {
      try {
        adminInfo.value = JSON.parse(savedAdminInfo)
      } catch (e) {
        console.error('Failed to parse admin info:', e)
      }
    }
  }

  restoreAuth()

  return {
    adminInfo,
    token,
    isLoggedIn,
    login,
    logout
  }
})
