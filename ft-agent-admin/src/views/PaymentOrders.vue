<template>
  <div class="payment-orders">
    <div class="header">
      <h2>支付订单管理</h2>
      <div class="header-actions">
        <el-select v-model="filterStatus" placeholder="订单状态" clearable style="width: 120px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option label="待支付" value="pending" />
          <el-option label="已支付" value="paid" />
          <el-option label="失败" value="failed" />
          <el-option label="已退款" value="refunded" />
        </el-select>
        <el-select v-model="filterChannel" placeholder="支付渠道" clearable style="width: 120px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option label="支付宝" value="alipay" />
          <el-option label="微信" value="wechat" />
        </el-select>
        <el-button @click="loadOrders" type="primary" plain>
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_id" label="订单号" min-width="180">
          <template #default="{ row }">
            <span class="order-id">{{ row.order_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="用户ID" min-width="140" show-overflow-tooltip />
        <el-table-column prop="order_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.order_type === 'recharge' ? 'success' : 'warning'" size="small">
              {{ row.order_type === 'recharge' ? '充值' : '订阅' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ (row.amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="token_amount" label="Token数量" width="110" align="right">
          <template #default="{ row }">
            {{ row.token_amount.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_channel" label="渠道" width="80">
          <template #default="{ row }">
            <el-tag :type="row.payment_channel === 'alipay' ? 'blue' : 'green'" size="small">
              {{ row.payment_channel === 'alipay' ? '支付宝' : '微信' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trade_no" label="交易号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_at" label="支付时间" width="150">
          <template #default="{ row }">
            {{ row.paid_at ? formatDate(row.paid_at) : '-' }}
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
          @current-change="loadOrders"
          @size-change="loadOrders"
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

const orders = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStatus = ref('')
const filterChannel = ref('')

const getStatusType = (status) => {
  const map = { pending: 'info', paid: 'success', failed: 'danger', refunded: 'warning' }
  return map[status] || 'info'
}

const getStatusName = (status) => {
  const map = { pending: '待支付', paid: '已支付', failed: '失败', refunded: '已退款' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadOrders = async () => {
  loading.value = true
  try {
    const filters = {}
    if (filterStatus.value) filters.status = filterStatus.value
    if (filterChannel.value) filters.channel = filterChannel.value

    const response = await api.getPaymentOrders(currentPage.value, pageSize.value, filters)
    if (response.status === 'success') {
      orders.value = response.data.orders || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载订单失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.payment-orders {
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
