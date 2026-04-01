<template>
  <div class="dashboard">
    <!-- 用户统计 -->
    <div class="section-title">用户概览</div>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_users || 0 }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.new_users_today || 0 }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.new_users_week || 0 }}</div>
              <div class="stat-label">本周新增</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #f56c6c;">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.zero_balance_users || 0 }}</div>
              <div class="stat-label">Token 耗尽用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Token 统计 -->
    <div class="section-title" style="margin-top: 30px;">Token 概览</div>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff;">
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
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><ShoppingCart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.total_purchased) }}</div>
              <div class="stat-label">累计购买</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #909399;">
              <el-icon><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.token_accounts || 0 }}</div>
              <div class="stat-label">Token 账户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 知识库统计 -->
    <div class="section-title" style="margin-top: 30px;">RAG 知识库</div>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_knowledge_files || 0 }}</div>
              <div class="stat-label">知识库文件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.indexed_files || 0 }}</div>
              <div class="stat-label">已索引文件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.tax_basic_vectors) }}</div>
              <div class="stat-label">Tax Basic 向量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #f56c6c;">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.tax_pro_vectors) }}</div>
              <div class="stat-label">Tax Pro 向量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 订阅 & Agent 分布 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>订阅统计</span>
          </template>
          <div class="stat-detail">
            <div class="detail-item">
              <span class="label">活跃订阅</span>
              <span class="value">{{ stats.active_subscriptions || 0 }}</span>
            </div>
            <div class="detail-item">
              <span class="label">总订阅数</span>
              <span class="value">{{ stats.total_subscriptions || 0 }}</span>
            </div>
            <div class="detail-item">
              <span class="label">订阅率</span>
              <span class="value">{{ subscriptionRate }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Agent 类型分布</span>
          </template>
          <div class="agent-distribution" v-if="Object.keys(stats.agent_distribution || {}).length">
            <div
              v-for="(count, name) in stats.agent_distribution"
              :key="name"
              class="agent-item"
            >
              <span class="agent-name">{{ name }}</span>
              <el-progress :percentage="getAgentPercentage(count)" :stroke-width="12">
                <span class="agent-count">{{ count }} 人</span>
              </el-progress>
            </div>
          </div>
          <div v-else class="empty-tip">暂无数据</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="stat-detail">
            <div class="detail-item">
              <span class="label">管理员数量</span>
              <span class="value">{{ stats.total_admins || 0 }} 人</span>
            </div>
            <div class="detail-item">
              <span class="label">系统版本</span>
              <span class="value">v1.0.0</span>
            </div>
            <div class="detail-item">
              <span class="label">Token 耗尽率</span>
              <span class="value">{{ zeroBalanceRate }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Token 使用率</span>
          </template>
          <div class="token-usage">
            <el-progress
              type="circle"
              :percentage="tokenUsageRate"
              :width="120"
              :stroke-width="10"
            >
              <template #default>
                <div class="usage-text">
                  <div class="usage-value">{{ tokenUsageRate }}%</div>
                  <div class="usage-label">已消耗</div>
                </div>
              </template>
            </el-progress>
            <div class="usage-detail">
              <div class="detail-item">
                <span class="label">已消耗</span>
                <span class="value">{{ formatNumber(stats.total_consumed) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">剩余</span>
                <span class="value">{{ formatNumber(stats.total_balance) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">总计</span>
                <span class="value">{{ formatNumber(totalToken) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import {
  User, Coin, TrendCharts, Calendar, UserFilled, CircleClose,
  ShoppingCart, Wallet, Document, SuccessFilled, Collection
} from '@element-plus/icons-vue'

const stats = ref({})

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(2) + 'K'
  return num.toString()
}

const totalToken = computed(() => {
  return (stats.value.total_balance || 0) + (stats.value.total_consumed || 0)
})

const tokenUsageRate = computed(() => {
  if (!totalToken.value) return 0
  return Math.round((stats.value.total_consumed || 0) / totalToken.value * 100)
})

const subscriptionRate = computed(() => {
  if (!stats.value.total_users) return 0
  return Math.round((stats.value.active_subscriptions || 0) / stats.value.total_users * 100)
})

const zeroBalanceRate = computed(() => {
  if (!stats.value.token_accounts) return 0
  return Math.round((stats.value.zero_balance_users || 0) / stats.value.token_accounts * 100)
})

const getAgentPercentage = (count) => {
  if (!stats.value.total_users) return 0
  return Math.round(count / stats.value.total_users * 100)
}

const loadStats = async () => {
  try {
    const response = await api.getOverview()
    if (response.status === 'success') {
      stats.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 4px solid #409eff;
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

.stat-detail {
  display: flex;
  flex-direction: column;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
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

.agent-distribution {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-name {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.agent-count {
  font-size: 12px;
  color: #909399;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 30px 0;
}

.token-usage {
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

.usage-detail .detail-item {
  padding: 8px 0;
}
</style>
