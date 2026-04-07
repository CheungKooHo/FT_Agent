<template>
  <el-container class="admin-layout">
    <el-aside width="200px">
      <div class="logo">
        <el-icon><Setting /></el-icon>
        <span>FT-Agent</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="admin-menu"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/policies">
          <el-icon><Document /></el-icon>
          <span>政策管理</span>
        </el-menu-item>
        <el-menu-item index="/tokens">
          <el-icon><Coin /></el-icon>
          <span>Token统计</span>
        </el-menu-item>
        <el-menu-item index="/conversation-stats">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话分析</span>
        </el-menu-item>
        <el-menu-item index="/agents">
          <el-icon><Operation /></el-icon>
          <span>Agent配置</span>
        </el-menu-item>
        <el-menu-item index="/tiers">
          <el-icon><PriceTag /></el-icon>
          <span>订阅版本</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/system-config">
          <el-icon><Tools /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-left">
          <h3>财税 Agent 管理后台</h3>
        </div>
        <div class="header-right">
          <span class="admin-name">{{ authStore.adminInfo?.username }}</span>
          <el-button @click="logout" size="small">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { Setting, DataAnalysis, User, Document, Coin, Operation, PriceTag, Collection, ChatDotRound, Tools } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const logout = () => {
  ElMessageBox.confirm('确定退出管理后台？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    authStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  border-bottom: 1px solid #404854;
}

.logo .el-icon {
  margin-right: 8px;
  font-size: 24px;
}

.admin-menu {
  border-right: none;
  background-color: #304156;
}

.admin-menu .el-menu-item {
  color: #bfcbd9;
}

.admin-menu .el-menu-item:hover,
.admin-menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.el-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left h3 {
  margin: 0;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-name {
  color: #606266;
  font-size: 14px;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
