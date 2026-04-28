<template>
  <div class="refund-requests">
    <div class="header">
      <h2>退款申请管理</h2>
      <div class="header-actions">
        <el-select v-model="filterStatus" placeholder="处理状态" clearable style="width: 120px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button @click="loadRequests" type="primary" plain>
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="requests" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="申请人" width="100" />
        <el-table-column prop="user_id" label="用户ID" min-width="140" show-overflow-tooltip />
        <el-table-column prop="order_id" label="订单号" min-width="180">
          <template #default="{ row }">
            <span class="order-id">{{ row.order_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="退款金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ (row.amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="token_amount" label="Token数量" width="110" align="right">
          <template #default="{ row }">
            {{ row.token_amount.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="退款原因" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="admin_note" label="管理员备注" min-width="120" show-overflow-tooltip />
        <el-table-column prop="created_at" label="申请时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
              <el-button size="small" type="danger" @click="handleReject(row)">拒绝</el-button>
            </template>
            <span v-else class="processed-text">已处理</span>
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
          @current-change="loadRequests"
          @size-change="loadRequests"
        />
      </div>
    </el-card>

    <!-- 拒绝原因对话框 -->
    <el-dialog v-model="showRejectDialog" title="拒绝退款" width="400px">
      <el-form>
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectNote" type="textarea" :rows="3" placeholder="请输入拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/api'

const requests = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStatus = ref('')
const showRejectDialog = ref(false)
const rejectNote = ref('')
const currentRejectRow = ref(null)

const getStatusType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getStatusName = (status) => {
  const map = { pending: '待处理', approved: '已通过', rejected: '已拒绝' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadRequests = async () => {
  loading.value = true
  try {
    const filters = {}
    if (filterStatus.value) filters.status = filterStatus.value

    const response = await api.getRefundRequests(currentPage.value, pageSize.value, filters)
    if (response.status === 'success') {
      requests.value = response.data.requests || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载退款申请失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定通过该退款申请吗？将扣除用户 ${row.token_amount.toLocaleString()} Token。`,
      '确认退款',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    const response = await api.approveRefund(row.id)
    if (response.status === 'success') {
      ElMessage.success('退款已通过')
      loadRequests()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleReject = (row) => {
  currentRejectRow.value = row
  rejectNote.value = ''
  showRejectDialog.value = true
}

const confirmReject = async () => {
  if (!currentRejectRow.value) return
  try {
    const response = await api.rejectRefund(currentRejectRow.value.id, rejectNote.value)
    if (response.status === 'success') {
      ElMessage.success('已拒绝退款申请')
      showRejectDialog.value = false
      loadRequests()
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  loadRequests()
})
</script>

<style scoped>
.refund-requests {
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

.order-id {
  font-size: 12px;
  font-family: monospace;
}

.processed-text {
  color: #909399;
  font-size: 13px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
