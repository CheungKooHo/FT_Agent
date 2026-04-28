<template>
  <div class="audit-logs">
    <div class="header">
      <h2>审计日志</h2>
      <div class="header-actions">
        <el-select v-model="filterAction" placeholder="操作类型" clearable style="width: 140px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option v-for="action in actionTypes" :key="action" :label="action" :value="action" />
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
        <el-button @click="loadLogs" type="primary" plain>
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="对象类型" width="100">
          <template #default="{ row }">
            {{ row.target_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="对象ID" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.target_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="details" label="详情" min-width="200">
          <template #default="{ row }">
            <span v-if="row.details" class="details-text">{{ formatDetails(row.details) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP" width="130" />
        <el-table-column prop="created_at" label="时间" width="160">
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
          :page-sizes="[50, 100, 200]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadLogs"
          @size-change="loadLogs"
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

const logs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const filterAction = ref('')
const dateRange = ref([])
const actionTypes = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatDetails = (details) => {
  try {
    const obj = JSON.parse(details)
    return Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ')
  } catch {
    return details
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const filters = {}
    if (filterAction.value) filters.action = filterAction.value
    if (dateRange.value && dateRange.value.length === 2) {
      filters.start_date = dateRange.value[0]
      filters.end_date = dateRange.value[1]
    }

    const response = await api.getAuditLogs(currentPage.value, pageSize.value, filters)
    if (response.status === 'success') {
      logs.value = response.data.logs || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载审计日志失败')
  } finally {
    loading.value = false
  }
}

const loadActionTypes = async () => {
  try {
    const response = await api.getAuditLogActions()
    if (response.status === 'success') {
      actionTypes.value = response.data || []
    }
  } catch (error) {
    console.error('加载操作类型失败', error)
  }
}

onMounted(() => {
  loadLogs()
  loadActionTypes()
})
</script>

<style scoped>
.audit-logs {
  padding: 0;
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
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
}

.details-text {
  font-size: 12px;
  color: #606266;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
