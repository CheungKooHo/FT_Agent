<template>
  <div class="profile-container">
    <!-- 用户信息卡片 -->
    <div class="profile-card user-info-card">
      <div class="card-header">
        <span>用户信息</span>
        <el-button type="primary" text size="small" @click="dialogVisible = true">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </div>

      <div class="user-profile">
        <div class="avatar-wrapper" @click="triggerAvatarUpload">
          <el-avatar :size="64" class="user-avatar" :src="form.avatar_url">
            {{ userStore.userInfo?.nickname?.charAt(0) || userStore.userInfo?.username?.charAt(0) }}
          </el-avatar>
          <div class="avatar-overlay">
            <el-icon><Camera /></el-icon>
          </div>
        </div>
        <input ref="avatarInput" type="file" accept="image/*" style="display: none;" @change="handleAvatarChange" />

        <div class="user-details">
          <div class="user-name">{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</div>
          <div class="user-bio" v-if="userStore.userInfo?.bio">{{ userStore.userInfo.bio }}</div>
          <div class="user-bio" v-else style="color: #c0c4cc;">暂无简介</div>
        </div>
      </div>

      <div class="info-list">
        <div class="info-row">
          <span class="info-label">用户ID</span>
          <span class="info-value user-id">{{ userStore.userInfo?.user_id }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ userStore.userInfo?.username }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">手机号</span>
          <span class="info-value">{{ userStore.userInfo?.phone || '未设置' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ formatDate(userStore.userInfo?.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 数据统计卡片 -->
    <div class="profile-card">
      <div class="card-header">
        <span>数据统计</span>
      </div>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #409EFF, #66B1FF);">
            <el-icon :size="24"><ChatLineRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.conversations }}</div>
            <div class="stat-label">对话轮次</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #67C23A, #85CE61);">
            <el-icon :size="24"><CollectionTag /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.memories }}</div>
            <div class="stat-label">记忆条数</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #E6A23C, #F56C6C);">
            <el-icon :size="24"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.days }}</div>
            <div class="stat-label">注册天数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 偏好设置卡片 -->
    <div class="profile-card">
      <div class="card-header">
        <span>偏好设置</span>
      </div>

      <div class="settings-list">
        <div class="setting-item">
          <div class="setting-info">
            <el-icon :size="20" color="#409EFF"><Bell /></el-icon>
            <span>消息提示音</span>
          </div>
          <el-switch v-model="soundEnabled" @change="toggleSound" />
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <el-icon :size="20" color="#67C23A"><Document /></el-icon>
            <span>自动保存草稿</span>
          </div>
          <el-switch v-model="autoSaveDraft" @change="toggleAutoSaveDraft" />
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <el-icon :size="20" color="#909399"><Moon /></el-icon>
            <span>深色模式</span>
          </div>
          <el-switch v-model="isDark" @change="toggleDarkMode" />
        </div>
      </div>
    </div>

    <!-- 编辑资料对话框 -->
    <el-dialog v-model="dialogVisible" title="编辑资料" width="90%" max-width="400px">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="请输入昵称" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号（可选）" />
        </el-form-item>

        <el-form-item label="个人简介">
          <el-input v-model="form.bio" type="textarea" :rows="2" placeholder="介绍一下自己（可选）" maxlength="100" show-word-limit />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound, CollectionTag, Clock, Bell, Document, Edit, Camera, Moon } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import api from '@/api'

const userStore = useUserStore()
const themeStore = useThemeStore()
const isDark = ref(themeStore.isDark)

const toggleDarkMode = () => {
  themeStore.toggleTheme()
}

const dialogVisible = ref(false)
const formRef = ref(null)
const avatarInput = ref(null)
const soundEnabled = ref(localStorage.getItem('soundEnabled') !== 'false')
const autoSaveDraft = ref(localStorage.getItem('autoSaveDraft') === 'true')

const stats = reactive({
  conversations: 0,
  memories: 0,
  days: 0
})

const form = reactive({
  nickname: '',
  email: '',
  phone: '',
  avatar_url: '',
  bio: ''
})

const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
    { required: false, message: '请输入邮箱', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
    { required: false }
  ]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const toggleSound = (enabled) => {
  localStorage.setItem('soundEnabled', String(enabled))
}

const toggleAutoSaveDraft = (enabled) => {
  localStorage.setItem('autoSaveDraft', String(enabled))
}

const triggerAvatarUpload = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return
  }

  // 简单处理：转为 base64 URL（生产环境应上传到 OSS）
  const reader = new FileReader()
  reader.onload = async (e) => {
    form.avatar_url = e.target.result
  }
  reader.readAsDataURL(file)
}

const loadStats = async () => {
  try {
    const userResponse = await api.getUserInfo(userStore.userInfo.user_id)
    if (userResponse.status === 'success') {
      userStore.userInfo = userResponse.data
      localStorage.setItem('userInfo', JSON.stringify(userResponse.data))
    }

    const historyResponse = await api.getConversationHistory(
      userStore.userInfo.user_id,
      { limit: 1000 }
    )
    if (historyResponse.status === 'success') {
      stats.conversations = historyResponse.data.length
    }

    const memoryResponse = await api.getUserMemories(userStore.userInfo.user_id)
    if (memoryResponse.status === 'success') {
      stats.memories = memoryResponse.data.length
    }

    if (userStore.userInfo?.created_at) {
      const createdAtStr = userStore.userInfo.created_at
      const createdAt = new Date(createdAtStr.replace(' ', 'T'))
      const now = new Date()
      const diffMs = now - createdAt
      const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      stats.days = Math.max(1, days)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await api.updateUserInfo(userStore.userInfo.user_id, {
          nickname: form.nickname,
          email: form.email || null,
          phone: form.phone || null,
          avatar_url: form.avatar_url || null,
          bio: form.bio || null
        })
        if (response.status === 'success') {
          userStore.userInfo = { ...userStore.userInfo, ...response.data }
          localStorage.setItem('userInfo', JSON.stringify(userStore.userInfo))
          ElMessage.success('更新成功')
          dialogVisible.value = false
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '更新失败')
      }
    }
  })
}

onMounted(() => {
  form.nickname = userStore.userInfo?.nickname || ''
  form.email = userStore.userInfo?.email || ''
  form.phone = userStore.userInfo?.phone || ''
  form.avatar_url = userStore.userInfo?.avatar_url || ''
  form.bio = userStore.userInfo?.bio || ''
  loadStats()
})
</script>

<style scoped>
.profile-container {
  height: 100%;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-sizing: border-box;
}

.profile-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
  cursor: pointer;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.user-avatar {
  background: linear-gradient(135deg, #409EFF, #67C23A);
  flex-shrink: 0;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.user-email {
  font-size: 12px;
  color: #909399;
}

.user-bio {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.info-list {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 13px;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid #f5f7fa;
}

.info-label {
  color: #909399;
  flex-shrink: 0;
}

.info-value {
  color: #606266;
  text-align: right;
  word-break: break-all;
}

.user-id {
  font-size: 11px;
  color: #c0c4cc;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 10px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-info {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.settings-list {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.setting-item:not(:last-child) {
  border-bottom: 1px solid #f5f7fa;
}

.setting-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

@media (min-width: 768px) {
  .profile-container {
    padding: 20px 24px;
    gap: 16px;
  }

  .profile-card {
    padding: 20px;
  }

  .card-header {
    font-size: 16px;
    margin-bottom: 20px;
  }

  .user-profile {
    gap: 20px;
    margin-bottom: 20px;
  }

  .user-avatar {
    width: 80px !important;
    height: 80px !important;
  }

  .user-name {
    font-size: 18px;
  }

  .info-row {
    padding: 10px 0;
    font-size: 14px;
  }

  .stats-grid {
    gap: 16px;
  }

  .stat-item {
    padding: 20px 16px;
  }

  .stat-icon {
    width: 52px;
    height: 52px;
  }

  .stat-value {
    font-size: 26px;
  }

  .stat-label {
    font-size: 13px;
  }

  .setting-item {
    padding: 14px 0;
  }
}
</style>
