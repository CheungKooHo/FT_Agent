<template>
  <div class="history-container">
    <div class="page-header">
      <div class="header-left">
        <el-select v-model="limit" size="default" class="limit-select">
          <el-option label="最近20条" :value="20" />
          <el-option label="最近50条" :value="50" />
          <el-option label="最近100条" :value="100" />
        </el-select>
      </div>
      <el-button type="danger" plain size="default" @click="handleClearAll">
        <el-icon><Delete /></el-icon>
        清空
      </el-button>
    </div>

    <div class="history-list" v-loading="loading">
      <el-empty v-if="!loading && historyList.length === 0" description="暂无历史记录">
        <el-button type="primary" @click="$router.push('/')">开始对话</el-button>
      </el-empty>

      <div v-else class="message-cards">
        <div
          v-for="(item, index) in historyList"
          :key="index"
          class="message-card"
          :class="item.role"
        >
          <div class="card-header">
            <el-avatar :size="28" :class="item.role === 'user' ? 'user-avatar' : 'ai-avatar'">
              <el-icon v-if="item.role === 'assistant'"><Robot /></el-icon>
              <span v-else>{{ userStore.userInfo?.nickname?.charAt(0) || '我' }}</span>
            </el-avatar>
            <span class="sender">{{ item.role === 'user' ? (userStore.userInfo?.nickname || '我') : '财税专家' }}</span>
            <span class="time">{{ item.time }}</span>
          </div>
          <div class="card-content">
            <MarkdownContent v-if="item.role === 'assistant'" :content="item.content" />
            <span v-else>{{ item.content }}</span>
          </div>
          <div class="card-actions">
            <el-button type="primary" text @click="copyContent(item.content)" class="copy-btn">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import MarkdownContent from '@/components/MarkdownContent.vue'

const userStore = useUserStore()

const historyList = ref([])
const limit = ref(50)
const loading = ref(false)

const copyContent = async (content) => {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(content)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = content
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const loadHistory = async () => {
  loading.value = true
  try {
    const res = await api.getConversationHistory(userStore.userInfo.user_id, {
      limit: limit.value
    })
    if (res.status === 'success') {
      historyList.value = res.data
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleClearAll = async () => {
  await ElMessageBox.confirm('确定要清空所有对话历史吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  try {
    await api.clearConversationHistory(userStore.userInfo.user_id)
    historyList.value = []
    ElMessage.success('已清空')
  } catch {
    ElMessage.error('清空失败')
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  padding: 16px;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.limit-select {
  width: 130px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.message-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-card {
  padding: 12px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
}

.message-card.user {
  background: #ecf5ff;
  border-color: #d9ecff;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sender {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

.time {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: auto;
}

.page-header :deep(.el-button) {
  padding: 8px;
}

.card-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  word-break: break-word;
}

.card-content :deep(p) {
  margin: 0;
}

.card-content :deep(p + p) {
  margin-top: 8px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.copy-btn {
  font-size: 12px;
  padding: 2px 8px;
  opacity: 0.5;
}

.copy-btn:hover {
  opacity: 1;
}

@media (max-width: 480px) {
  .copy-btn {
    opacity: 0.6;
  }
}

.user-avatar {
  background: #409eff;
}

.ai-avatar {
  background: #67c23a;
}

@media (min-width: 768px) {
  .history-container {
    padding: 20px 24px;
  }

  .page-header {
    margin-bottom: 20px;
  }

  .message-card {
    padding: 16px;
  }

  .card-content {
    font-size: 14px;
  }
}
</style>
