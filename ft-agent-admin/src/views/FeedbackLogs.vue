<template>
  <div class="feedback-logs">
    <div class="header">
      <h2>评价记录</h2>
      <div class="header-actions">
        <el-select v-model="filterRating" placeholder="评价类型" clearable style="width: 120px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option label="好评" value="like" />
          <el-option label="差评" value="dislike" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="margin-right: 10px;"
        />
        <el-button @click="loadFeedback" type="primary" plain>
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总评价数</div>
      </el-card>
      <el-card class="stat-card success">
        <div class="stat-value">{{ stats.likes }}</div>
        <div class="stat-label">好评数</div>
      </el-card>
      <el-card class="stat-card danger">
        <div class="stat-value">{{ stats.dislikes }}</div>
        <div class="stat-label">差评数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.likeRate }}%</div>
        <div class="stat-label">好评率</div>
      </el-card>
    </div>

    <el-card>
      <el-table :data="feedbacks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="user_id" label="用户ID" width="180" show-overflow-tooltip />
        <el-table-column prop="session_id" label="会话ID" width="180" show-overflow-tooltip />
        <el-table-column prop="message_index" label="消息索引" width="100" />
        <el-table-column prop="rating" label="评分" width="80">
          <template #default="{ row }">
            <el-tag :type="row.rating === 'like' ? 'success' : 'danger'" size="small">
              {{ row.rating === 'like' ? '好评' : '差评' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="差评原因" min-width="150">
          <template #default="{ row }">
            <span v-if="row.reason">{{ row.reason }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="评价时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadFeedback"
          @size-change="loadFeedback"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/api'

const feedbacks = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const filterRating = ref('')
const dateRange = ref([])
const stats = ref({ total: 0, likes: 0, dislikes: 0, likeRate: 0 })

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

const loadFeedback = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterRating.value) params.rating = filterRating.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await api.adminGetFeedbackList(params)
    if (res.status === 'success') {
      feedbacks.value = res.data.list
      total.value = res.data.total
      stats.value = res.data.stats
    }
  } catch (error) {
    console.error('加载评价记录失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFeedback()
})
</script>

<style scoped>
.feedback-logs {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
}

.stats-cards {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  text-align: center;
  padding: 10px;
}

.stat-card.success .stat-value {
  color: #67c23a;
}

.stat-card.danger .stat-value {
  color: #f56c6c;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>