<template>
  <el-container class="main-layout">
    <!-- 侧边栏遮罩层 -->
    <div
      v-if="isMobile && sidebarVisible"
      class="sidebar-overlay"
      @click="sidebarVisible = false"
    ></div>

    <!-- 侧边栏 -->
    <el-aside
      :width="isMobile ? '260px' : '220px'"
      class="sidebar"
      :class="{ 'sidebar-hidden': isMobile && !sidebarVisible }"
    >
      <div class="logo">
        <div class="logo-icon">
          <el-icon :size="24"><ChatDotRound /></el-icon>
        </div>
        <div class="logo-text">
          <span class="logo-title">财税助手</span>
          <span class="logo-subtitle">智能AI平台</span>
        </div>
      </div>

      <div class="menu-section">
        <div class="menu-title">导航</div>
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          @select="onMenuSelect"
        >
          <el-menu-item index="/">
            <el-icon><ChatLineRound /></el-icon>
            <span>智能对话</span>
          </el-menu-item>

          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库</span>
          </el-menu-item>

          <el-menu-item index="/memory">
            <el-icon><CollectionTag /></el-icon>
            <span>我的记忆</span>
          </el-menu-item>

          <el-menu-item index="/history">
            <el-icon><ChatLineSquare /></el-icon>
            <span>历史记录</span>
          </el-menu-item>

          <el-menu-item index="/billing">
            <el-icon><Coin /></el-icon>
            <span>账户与订阅</span>
          </el-menu-item>

          <el-menu-item index="/profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="sidebar-footer">
        <div class="user-card">
          <el-avatar :size="40" class="user-avatar">
            {{
              userStore.userInfo?.nickname?.charAt(0) ||
              userStore.userInfo?.username?.charAt(0)
            }}
          </el-avatar>
          <div class="user-info">
            <div class="user-name">
              {{ userStore.userInfo?.nickname || userStore.userInfo?.username }}
            </div>
            <div class="user-tier">
              {{ billingStore.subscription?.tier_name || "基础版" }}
            </div>
          </div>
          <el-dropdown @command="handleCommand" trigger="click">
            <el-icon class="logout-icon"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <el-header class="main-header">
        <div class="header-left">
          <el-icon
            v-if="isMobile"
            class="hamburger"
            @click="sidebarVisible = !sidebarVisible"
          >
            <component :is="sidebarVisible ? 'Close' : 'Expand'" />
          </el-icon>
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>
        <div class="header-right">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-badge">
            <el-icon class="notif-icon" @click="showNotificationPanel = true"><Bell /></el-icon>
          </el-badge>
          <div class="token-badge">
            <el-icon><Coin /></el-icon>
            <span class="token-text"
              >{{ billingStore.tokenBalance }} Token</span
            >
          </div>
          <el-dropdown @command="handleLanguageChange" trigger="click">
            <el-icon class="lang-icon"><Translate /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-CN" :disabled="locale === 'zh-CN'">
                  <span>中文</span>
                </el-dropdown-item>
                <el-dropdown-item command="en-US" :disabled="locale === 'en-US'">
                  <span>English</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>

      <!-- 通知面板 -->
      <el-drawer v-model="showNotificationPanel" title="通知中心" direction="rtl" size="380px">
        <div class="notification-panel">
          <div class="notif-header">
            <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0">全部已读</el-button>
          </div>
          <div v-if="notifications.length === 0" class="notif-empty">
            <el-empty description="暂无通知" :image-size="80" />
          </div>
          <div v-else class="notif-list">
            <div
              v-for="item in notifications"
              :key="item.id"
              class="notif-item"
              :class="{ unread: !item.is_read }"
              @click="handleNotifClick(item)"
            >
              <div class="notif-icon-wrap">
                <el-icon v-if="item.notification_type === 'system'"><InfoFilled /></el-icon>
                <el-icon v-else-if="item.notification_type === 'subscription'"><Tickets /></el-icon>
                <el-icon v-else><Bell /></el-icon>
              </div>
              <div class="notif-content">
                <div class="notif-title">{{ item.title }}</div>
                <div class="notif-text">{{ item.content }}</div>
                <div class="notif-time">{{ formatTime(item.created_at) }}</div>
              </div>
              <div v-if="!item.is_read" class="notif-dot"></div>
            </div>
          </div>
        </div>
      </el-drawer>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessageBox, ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/stores/user";
import { useBillingStore } from "@/stores/billing";
import api from "@/api";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const billingStore = useBillingStore();
const { locale } = useI18n();

const isMobile = ref(false);
const sidebarVisible = ref(false);
const showNotificationPanel = ref(false);
const notifications = ref([]);
const unreadCount = ref(0);

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768;
  if (!isMobile.value) {
    sidebarVisible.value = false;
  }
};

onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
  loadUnreadCount();
});

watch(showNotificationPanel, (val) => {
  if (val) loadNotifications();
});

onUnmounted(() => {
  window.removeEventListener("resize", checkMobile);
});

const activeMenu = computed(() => route.path);

const pageTitle = computed(() => {
  const map = {
    "/": "智能对话",
    "/knowledge": "知识库管理",
    "/memory": "我的记忆",
    "/history": "对话历史",
    "/billing": "账户与订阅",
    "/profile": "个人中心",
  };
  return map[route.path] || "财税助手";
});

const onMenuSelect = () => {
  if (isMobile.value) {
    sidebarVisible.value = false;
  }
};

const handleCommand = async (command) => {
  if (command === "logout") {
    await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    userStore.logout();
    router.push("/login");
  }
};

const handleLanguageChange = (lang) => {
  locale.value = lang;
  localStorage.setItem('locale', lang);
  ElMessage.success(lang === 'zh-CN' ? '语言已切换为中文' : 'Language changed to English');
};

const loadUnreadCount = async () => {
  if (!userStore.userInfo?.user_id) return;
  try {
    const res = await api.getUnreadCount(userStore.userInfo.user_id);
    if (res.status === 'success') {
      unreadCount.value = res.data.count;
    }
  } catch (e) {
    // ignore
  }
};

const loadNotifications = async () => {
  if (!userStore.userInfo?.user_id) return;
  try {
    const res = await api.getNotifications(userStore.userInfo.user_id);
    if (res.status === 'success') {
      notifications.value = res.data;
    }
  } catch (e) {
    // ignore
  }
};

const handleNotifClick = async (item) => {
  if (!item.is_read) {
    try {
      await api.markAsRead(item.id, userStore.userInfo.user_id);
      item.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch (e) {
      // ignore
    }
  }
};

const markAllRead = async () => {
  if (!userStore.userInfo?.user_id) return;
  try {
    await api.markAllAsRead(userStore.userInfo.user_id);
    notifications.value.forEach(n => n.is_read = true);
    unreadCount.value = 0;
  } catch (e) {
    // ignore
  }
};

const formatTime = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  const now = new Date();
  const diff = now - d;
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
  return d.toLocaleDateString('zh-CN');
};
</script>

<style scoped>
.main-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: row;
  background: #f0f2f5;
  overflow: hidden;
}

/* 移动端适配 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: none;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

@media (max-width: 767px) {
  .main-layout {
    height: 100dvh;
    width: 100%;
    overflow: hidden;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 260px;
    z-index: 1000;
  }

  .sidebar-hidden {
    transform: translateX(-100%);
  }

  .sidebar-overlay {
    display: block;
  }

  .main-container {
    display: flex;
    flex-direction: column;
    flex: 1;
    width: 100%;
    min-width: 0;
    overflow: hidden;
  }

  .main-header {
    height: 56px;
    padding: 0 16px;
    width: 100%;
  }

  .page-title {
    font-size: 16px;
  }

  .main-content {
    padding: 12px;
    flex: 1;
    width: 100%;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
  }

  :deep(.el-main) {
    padding: 12px;
    flex: 1;
    width: 100%;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
  }
}

.logo {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.logo-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 2px;
}

.menu-section {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.menu-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 0 12px;
  margin-bottom: 8px;
}

.sidebar-menu {
  background: transparent;
  border: none;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  margin-bottom: 4px;
  transition: all 0.3s;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: #fff;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.sidebar-menu .el-menu-item .el-icon {
  margin-right: 10px;
  font-size: 18px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: background 0.3s;
}

.user-card:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-tier {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.logout-icon {
  color: #fff !important;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: color 0.3s;
}

.logout-icon:hover {
  color: rgba(255, 255, 255, 0.7) !important;
}

.main-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.main-header {
  height: 64px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hamburger {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #fdf6ec, #fef0e6);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  color: #e6a23c;
}

.token-text {
  white-space: nowrap;
}

.lang-icon {
  font-size: 18px;
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}

.lang-icon:hover {
  color: #409eff;
}

.main-content {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  width: 100%;
}

:deep(.el-main) {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

@media (max-width: 767px) {
  .main-content {
    padding: 12px;
  }

  :deep(.el-main) {
    padding: 12px;
  }
}

@media (min-width: 768px) {
  .main-header {
    padding: 0 32px;
  }

  .page-title {
    font-size: 20px;
  }

  .token-badge {
    padding: 8px 16px;
    font-size: 13px;
    gap: 6px;
  }

  .main-content {
    padding: 24px 32px;
  }
}

:deep(.el-main) {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

@media (min-width: 768px) {
  .main-header {
    padding: 0 32px;
  }

  .page-title {
    font-size: 20px;
  }

  .token-badge {
    padding: 8px 16px;
    font-size: 13px;
    gap: 6px;
  }

  .main-content {
    padding: 24px 32px;
  }
}

/* 通知铃铛 */
.notification-badge {
  cursor: pointer;
}

.notif-icon {
  font-size: 20px;
  color: #606266;
  cursor: pointer;
  transition: color 0.3s;
}

.notif-icon:hover {
  color: #409eff;
}

/* 通知面板 */
.notification-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notif-header {
  padding: 0 0 12px 0;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
}

.notif-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notif-list {
  flex: 1;
  overflow-y: auto;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 4px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.notif-item:hover {
  background: #f5f7fa;
}

.notif-item.unread {
  background: #f0f9ff;
}

.notif-item.unread:hover {
  background: #e6f4ff;
}

.notif-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #409eff;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.notif-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: 11px;
  color: #909399;
  margin-top: 6px;
}

.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  flex-shrink: 0;
  margin-top: 4px;
}

/* 深色模式通知 */
.dark .notif-header {
  border-color: #2d2d2d;
}

.dark .notif-item {
  border-color: #2d2d2d;
}

.dark .notif-item:hover {
  background: #242424;
}

.dark .notif-item.unread {
  background: rgba(64, 158, 255, 0.08);
}

.dark .notif-item.unread:hover {
  background: rgba(64, 158, 255, 0.12);
}

.dark .notif-icon-wrap {
  background: rgba(64, 158, 255, 0.15);
}

.dark .notif-title {
  color: #e5e5e5;
}

.dark .notif-text {
  color: #b0b0b0;
}

.dark .notif-time {
  color: #707070;
}
</style>