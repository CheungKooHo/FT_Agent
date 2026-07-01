<template>
  <div class="favorites-container">
    <div class="page-header">
      <h2>我的收藏</h2>
    </div>

    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载中...
    </div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <el-icon :size="60" color="#dcdfe6"><Star /></el-icon>
      <p>暂无收藏内容</p>
      <p class="hint">在对话中点击收藏按钮来保存感兴趣的回答</p>
    </div>

    <div v-else class="favorites-list">
      <div v-for="item in favorites" :key="item.id" class="favorite-card">
        <div class="card-header">
          <span class="card-time">{{ formatDate(item.created_at) }}</span>
          <el-button type="danger" text size="small" @click="handleDelete(item.id)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
        <div class="card-content">
          <MarkdownContent :content="item.content" />
        </div>
        <div v-if="item.source" class="card-source">
          <el-tag size="small" type="info">{{ item.source }}</el-tag>
        </div>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchFavorites"
      />
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
const favorites = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchFavorites = async () => {
  loading.value = true
  try {
    const res = await api.getFavorites(currentPage.value, pageSize.value)
    if (res.status === 'success') {
      favorites.value = res.data.favorites
      total.value = res.data.total
    }
  } catch (e) {
    console.error('获取收藏失败', e)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这条收藏？', '提示', { type: 'warning' })
    await api.deleteFavorite(id)
    ElMessage.success('已删除')
    fetchFavorites()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchFavorites()
})
</script>

<style scoped>
.favorites-container {
  height: 100%;
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60%;
  color: #909399;
  gap: 12px;
}

.empty-state {
  height: 60%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
}

.empty-state p {
  margin: 12px 0 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #c0c4cc;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.favorite-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-time {
  font-size: 12px;
  color: #909399;
}

.card-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.card-source {
  margin-top: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (min-width: 768px) {
  .favorites-container {
    padding: 24px;
  }

  .page-header h2 {
    font-size: 20px;
  }
}

.dark .favorite-card {
  background: var(--view-bg);
  border: 1px solid var(--view-border);
}

.dark .card-content {
  color: var(--view-text-primary);
}
</style>
