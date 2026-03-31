import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'
import { useUserStore } from './user'

export const useBillingStore = defineStore('billing', () => {
  const tokenBalance = ref(0)
  const subscription = ref(null)
  const transactions = ref([])
  const availableTiers = ref([])
  const tokenPrice = ref({ price_per_million: 500, price_yuan: 5 }) // 默认5元/百万

  // 获取 Token 价格
  async function fetchTokenPrice() {
    try {
      const response = await api.getTokenPrice()
      if (response.status === 'success') {
        tokenPrice.value = response.data
      }
    } catch (error) {
      console.error('获取Token价格失败:', error)
    }
  }

  // 获取 Token 余额
  async function fetchTokenBalance() {
    const userStore = useUserStore()
    if (!userStore.userInfo?.user_id) return

    try {
      const response = await api.getTokenBalance(userStore.userInfo.user_id)
      if (response.status === 'success') {
        tokenBalance.value = response.data.balance
      }
    } catch (error) {
      console.error('获取Token余额失败:', error)
    }
  }

  // 获取订阅信息
  async function fetchSubscription() {
    const userStore = useUserStore()
    if (!userStore.userInfo?.user_id) return

    try {
      const response = await api.getSubscription(userStore.userInfo.user_id)
      if (response.status === 'success') {
        subscription.value = response.data
      }
    } catch (error) {
      console.error('获取订阅信息失败:', error)
    }
  }

  // 获取交易记录
  async function fetchTransactions(limit = 50) {
    const userStore = useUserStore()
    if (!userStore.userInfo?.user_id) return

    try {
      const response = await api.getTokenTransactions(userStore.userInfo.user_id, limit)
      if (response.status === 'success') {
        transactions.value = response.data
      }
    } catch (error) {
      console.error('获取交易记录失败:', error)
    }
  }

  // 获取可用订阅等级
  async function fetchAvailableTiers() {
    try {
      const response = await api.getTiers()
      if (response.status === 'success') {
        availableTiers.value = response.data
      }
    } catch (error) {
      console.error('获取订阅等级失败:', error)
    }
  }

  // 充值 Token
  async function rechargeToken(amount) {
    const userStore = useUserStore()
    if (!userStore.userInfo?.user_id) {
      return { success: false, message: '用户未登录' }
    }

    try {
      const response = await api.rechargeToken(userStore.userInfo.user_id, amount)
      if (response.status === 'success') {
        tokenBalance.value = response.data.balance
        return { success: true }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 升级订阅
  async function upgradeSubscription(tierCode) {
    const userStore = useUserStore()
    if (!userStore.userInfo?.user_id) {
      return { success: false, message: '用户未登录' }
    }

    try {
      const response = await api.upgradeSubscription(userStore.userInfo.user_id, tierCode)
      if (response.status === 'success') {
        await fetchSubscription()
        return { success: true }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  // 初始化（获取所有信息）
  async function init() {
    await Promise.all([
      fetchTokenPrice(),
      fetchTokenBalance(),
      fetchSubscription(),
      fetchAvailableTiers()
    ])
  }

  return {
    tokenBalance,
    subscription,
    transactions,
    availableTiers,
    tokenPrice,
    fetchTokenPrice,
    fetchTokenBalance,
    fetchSubscription,
    fetchTransactions,
    fetchAvailableTiers,
    rechargeToken,
    upgradeSubscription,
    init
  }
})
