<template>
  <div class="notifications-page">
    <div class="page-header">
      <h2>通知管理</h2>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-num">{{ stats.total }}</div>
        <div class="stat-label">总通知数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-num">{{ stats.unread }}</div>
        <div class="stat-label">未读</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-num">{{ stats.read }}</div>
        <div class="stat-label">已读</div>
      </el-card>
    </div>

    <!-- 筛选和操作 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="类型">
          <el-select v-model="filter.type" placeholder="全部" clearable style="width: 150px">
            <el-option label="系统通知" value="system" />
            <el-option label="订阅通知" value="subscription" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.isRead" placeholder="全部" clearable style="width: 120px">
            <el-option label="未读" value="false" />
            <el-option label="已读" value="true" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="filter.dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width: 240px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 通知列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="list-header">
          <span>通知列表</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">发送通知</el-button>
          <el-button type="danger" size="small" @click="showBroadcastDialog = true">广播通知</el-button>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user_id" label="用户ID" width="180" show-overflow-tooltip />
        <el-table-column prop="notification_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.notification_type === 'system'" type="info">系统</el-tag>
            <el-tag v-else-if="row.notification_type === 'subscription'" type="success">订阅</el-tag>
            <el-tag v-else type="warning">其他</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="is_read" label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_read" type="info" size="small">已读</el-tag>
            <el-tag v-else type="danger" size="small">未读</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next"
          @update:current-page="pagination.page = $event; loadData()"
          @update:page-size="pagination.pageSize = $event; loadData()"
        />
      </div>
    </el-card>

    <!-- 发送单个通知弹窗 -->
    <el-dialog v-model="showCreateDialog" title="发送通知" width="450px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户ID" required>
          <el-input v-model="createForm.user_id" placeholder="请输入用户ID" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="createForm.notification_type" style="width: 100%">
            <el-option label="系统通知" value="system" />
            <el-option label="订阅通知" value="subscription" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="通知标题" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="createForm.content" type="textarea" :rows="3" placeholder="通知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleCreate">发送</el-button>
      </template>
    </el-dialog>

    <!-- 广播通知弹窗 -->
    <el-dialog v-model="showBroadcastDialog" title="广播通知" width="450px">
      <el-form :model="broadcastForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="broadcastForm.notification_type" style="width: 100%">
            <el-option label="系统通知" value="system" />
            <el-option label="订阅通知" value="subscription" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="broadcastForm.title" placeholder="通知标题" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="broadcastForm.content" type="textarea" :rows="3" placeholder="通知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBroadcastDialog = false">取消</el-button>
        <el-button type="warning" :loading="submitLoading" @click="handleBroadcast">确认广播</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api'

const loading = ref(false)
const submitLoading = ref(false)
const list = ref([])
const stats = ref({ total: 0, unread: 0, read: 0 })
const showCreateDialog = ref(false)
const showBroadcastDialog = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

const filter = reactive({
  type: '',
  isRead: '',
  dateRange: []
})

const createForm = reactive({
  user_id: '',
  notification_type: 'system',
  title: '',
  content: ''
})

const broadcastForm = reactive({
  notification_type: 'system',
  title: '',
  content: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filter.type) params.notification_type = filter.type
    if (filter.isRead) params.is_read = filter.isRead
    if (filter.dateRange?.length === 2) {
      params.start_date = filter.dateRange[0]
      params.end_date = filter.dateRange[1]
    }

    const res = await api.getNotificationList(params)
    if (res.status === 'success') {
      list.value = res.data.list
      pagination.total = res.data.total
    }

    const statsRes = await api.getNotificationStats()
    if (statsRes.status === 'success') {
      stats.value = statsRes.data
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.type = ''
  filter.isRead = ''
  filter.dateRange = []
  pagination.page = 1
  loadData()
}

const handleCreate = async () => {
  if (!createForm.user_id || !createForm.title || !createForm.content) {
    ElMessage.warning('请填写完整信息')
    return
  }
  submitLoading.value = true
  try {
    const res = await api.createNotification(createForm)
    if (res.status === 'success') {
      ElMessage.success('通知已发送')
      showCreateDialog.value = false
      Object.assign(createForm, { user_id: '', notification_type: 'system', title: '', content: '' })
      loadData()
    }
  } catch (e) {
    ElMessage.error('发送失败')
  } finally {
    submitLoading.value = false
  }
}

const handleBroadcast = async () => {
  if (!broadcastForm.title || !broadcastForm.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  submitLoading.value = true
  try {
    const res = await api.broadcastNotification(broadcastForm)
    if (res.status === 'success') {
      ElMessage.success(res.message)
      showBroadcastDialog.value = false
      Object.assign(broadcastForm, { notification_type: 'system', title: '', content: '' })
      loadData()
    }
  } catch (e) {
    ElMessage.error('广播失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定删除该通知？', '提示', { type: 'warning' }).then(async () => {
    try {
      await api.deleteNotification(id)
      ElMessage.success('删除成功')
      loadData()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const formatTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat-card {
  flex: 1;
  text-align: center;
}

.stat-num {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.filter-card .list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-card {
  flex: 1;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>