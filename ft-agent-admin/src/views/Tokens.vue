<template>
  <div class="tokens">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.total_balance) }}</div>
              <div class="stat-label">剩余 Token</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #f56c6c;">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.total_consumed) }}</div>
              <div class="stat-label">已消耗 Token</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon><ShoppingCart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.total_purchased) }}</div>
              <div class="stat-label">累计购买 Token</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.zero_balance_accounts || 0 }}</div>
              <div class="stat-label">Token 耗尽用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 版本分布 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>各版本 Token 分布</span>
          </template>
          <el-table :data="tierStatsData" stripe size="small">
            <el-table-column prop="tier_name" label="版本" />
            <el-table-column prop="count" label="用户数" align="center" />
            <el-table-column prop="balance" label="剩余 Token" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.balance) }}
              </template>
            </el-table-column>
            <el-table-column prop="consumed" label="已消耗" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.consumed) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Token 使用率</span>
          </template>
          <div class="usage-overview">
            <el-progress
              type="circle"
              :percentage="usageRate"
              :width="120"
              :stroke-width="10"
            >
              <template #default>
                <div class="usage-text">
                  <div class="usage-value">{{ usageRate }}%</div>
                  <div class="usage-label">已消耗</div>
                </div>
              </template>
            </el-progress>
            <div class="usage-detail">
              <div class="detail-item">
                <span class="label">总 Token</span>
                <span class="value">{{ formatNumber(stats.total_balance + stats.total_consumed) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">剩余</span>
                <span class="value" style="color: #67c23a;">{{ formatNumber(stats.total_balance) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">已消耗</span>
                <span class="value" style="color: #f56c6c;">{{ formatNumber(stats.total_consumed) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">账户数</span>
                <span class="value">{{ stats.total_accounts || 0 }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Top 消费者 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>Top 20 Token 消费者</span>
      </template>
      <el-table :data="topConsumers" stripe>
        <el-table-column prop="username" label="用户" min-width="15%">
          <template #default="{ row }">
            <span class="username">{{ row.username }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="用户ID" min-width="20%" show-overflow-tooltip />
        <el-table-column prop="balance" label="剩余 Token" min-width="15%" align="right">
          <template #default="{ row }">
            <span :class="['token-balance', { 'zero': row.balance === 0 }]">
              {{ formatNumber(row.balance) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_purchased" label="累计购买" min-width="15%" align="right">
          <template #default="{ row }">
            <span>{{ formatNumber(row.total_purchased) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_consumed" label="累计消耗" min-width="15%" align="right">
          <template #default="{ row }">
            <span class="consumed">{{ formatNumber(row.total_consumed) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="消耗占比" min-width="20%">
          <template #default="{ row }">
            <el-progress
              :percentage="getConsumeRate(row.total_consumed)"
              :stroke-width="8"
              :color="getProgressColor(getConsumeRate(row.total_consumed))"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 最近交易 -->
    <el-card>
      <template #header>
        <span>最近 Token 交易</span>
      </template>
      <el-table :data="recentTransactions" stripe size="small">
        <el-table-column prop="created_at" label="时间" min-width="18%">
          <template #default="{ row }">
            <span class="muted">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" min-width="15%" />
        <el-table-column prop="type" label="类型" min-width="10%" align="center">
          <template #default="{ row }">
            <el-tag :type="getTransactionTypeColor(row.type)" size="small">
              {{ getTransactionTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="变动" min-width="12%" align="right">
          <template #default="{ row }">
            <span :class="['amount', row.amount > 0 ? 'positive' : 'negative']">
              {{ row.amount > 0 ? '+' : '' }}{{ formatNumber(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="余额" min-width="12%" align="right">
          <template #default="{ row }">
            <span>{{ formatNumber(row.balance_after) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="33%" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Coin, TrendCharts, ShoppingCart, Warning } from '@element-plus/icons-vue'
import api from '@/api'

const stats = ref({})
const topConsumers = ref([])
const recentTransactions = ref([])
const tierStatsData = ref([])
const loading = ref(false)

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(2) + 'K'
  return num.toString()
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const totalToken = computed(() => {
  return (stats.value.total_balance || 0) + (stats.value.total_consumed || 0)
})

const usageRate = computed(() => {
  if (!totalToken.value) return 0
  return Math.round((stats.value.total_consumed || 0) / totalToken.value * 100)
})

const getConsumeRate = (consumed) => {
  if (!stats.value.total_consumed) return 0
  return Math.round(consumed / (stats.value.total_consumed + stats.value.total_balance) * 100)
}

const getProgressColor = (percentage) => {
  if (percentage < 30) return '#67c23a'
  if (percentage < 70) return '#e6a23c'
  return '#f56c6c'
}

const getTransactionTypeColor = (type) => {
  const map = { purchase: 'success', grant: 'primary', consume: 'warning', refund: 'info' }
  return map[type] || 'info'
}

const getTransactionTypeName = (type) => {
  const map = { purchase: '购买', grant: '赠送', consume: '消耗', refund: '退款' }
  return map[type] || type
}

const loadStats = async () => {
  loading.value = true
  try {
    const response = await api.getTokenStats()
    if (response.status === 'success') {
      stats.value = response.data.summary || {}
      topConsumers.value = response.data.top_consumers || []
      recentTransactions.value = response.data.recent_transactions || []
      tierStatsData.value = Object.entries(response.data.tier_stats || {}).map(([name, data]) => ({
        tier_name: name,
        ...data
      }))
    }
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.tokens {
  padding: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 26px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

.usage-overview {
  display: flex;
  align-items: center;
  gap: 40px;
}

.usage-text {
  text-align: center;
}

.usage-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.usage-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.usage-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  color: #909399;
}

.detail-item .value {
  font-weight: bold;
  color: #303133;
}

.username {
  font-weight: 500;
}

.token-balance {
  font-weight: 600;
  color: #303133;
}

.token-balance.zero {
  color: #f56c6c;
}

.consumed {
  color: #f56c6c;
  font-weight: 500;
}

.muted {
  color: #909399;
  font-size: 13px;
}

.amount {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.amount.positive {
  color: #67c23a;
}

.amount.negative {
  color: #f56c6c;
}
</style>
