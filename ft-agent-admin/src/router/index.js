import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'AdminLogin',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      },
      {
        path: 'tokens',
        name: 'Tokens',
        component: () => import('@/views/Tokens.vue')
      },
      {
        path: 'conversation-stats',
        name: 'ConversationStats',
        component: () => import('@/views/ConversationStats.vue')
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/Agents.vue')
      },
      {
        path: 'tiers',
        name: 'Tiers',
        component: () => import('@/views/Tiers.vue')
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue')
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('@/views/SystemConfig.vue')
      },
      {
        path: 'payment-orders',
        name: 'PaymentOrders',
        component: () => import('@/views/PaymentOrders.vue')
      },
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('@/views/AuditLogs.vue')
      },
      {
        path: 'refund-requests',
        name: 'RefundRequests',
        component: () => import('@/views/RefundRequests.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
