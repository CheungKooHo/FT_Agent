<template>
  <div class="conversation-stats">
    <!-- 摘要卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.total_conversations) }}</div>
              <div class="stat-label">总对话消息</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_users_with_chat || 0 }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.avg_messages_per_user) }}</div>
              <div class="stat-label">人均消息数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #909399;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.silent_users || 0 }}</div>
              <div class="stat-label">沉默用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 时间维度统计 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="time-stat">
            <div class="time-value">{{ formatNumber(timeStats.today_messages) }}</div>
            <div class="time-label">今日消息</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="time-stat">
            <div class="time-value">{{ formatNumber(timeStats.week_messages) }}</div>
            <div class="time-label">本周消息</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="time-stat">
            <div class="time-value">{{ formatNumber(timeStats.month_messages) }}</div>
            <div class="time-label">本月消息</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 对话趋势图 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>每日对话消息趋势（近30天）</span>
          </template>
          <div class="chart-container" ref="messageChartRef"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>Agent 类型分布</span>
          </template>
          <div class="chart-container" ref="agentChartRef" v-if="Object.keys(agentDistribution).length"></div>
          <div v-else class="empty">暂无数据</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Token 消耗趋势 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>每日 Token 消耗趋势（近30天）</span>
          </template>
          <div class="chart-container" ref="tokenChartRef"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, User, TrendCharts, Warning } from '@element-plus/icons-vue'
import api from '@/api'

const stats = ref({})
const timeStats = ref({})
const agentDistribution = ref({})
const dailyTrend = ref([])
const dailyTokenTrend = ref([])
const loading = ref(false)

let messageChart = null
let tokenChart = null
let agentChart = null
const messageChartRef = ref(null)
const tokenChartRef = ref(null)
const agentChartRef = ref(null)

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const getAgentPercent = (count) => {
  if (!stats.value.total_conversations) return 0
  return Math.round(count / stats.value.total_conversations * 100)
}

const getAgentColor = (agent) => {
  const colors = {
    'tax_basic': '#409eff',
    'tax_pro': '#67c23a',
    'unknown': '#909399'
  }
  return colors[agent] || '#e6a23c'
}

const getChartOption = (data, label, color) => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const p = params[0]
      return `${p.name}<br/>${label}: ${formatNumber(p.value)}`
    }
  },
  xAxis: {
    type: 'category',
    data: data.map(d => d.date.slice(5)),
    axisLabel: { rotate: 45, fontSize: 10 }
  },
  yAxis: { type: 'value' },
  series: [{
    data: data.map(d => d[Object.keys(d).find(k => k !== 'date')]),
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.2 },
    lineStyle: { color },
    itemStyle: { color },
    showSymbol: false
  }],
  grid: { left: 50, right: 20, top: 20, bottom: 50 }
})

const initCharts = async () => {
  const echarts = await import('echarts')
  if (messageChartRef.value) {
    messageChart = echarts.init(messageChartRef.value)
    messageChart.setOption(getChartOption(dailyTrend.value, '消息数', '#409eff'))
  }
  if (tokenChartRef.value) {
    tokenChart = echarts.init(tokenChartRef.value)
    tokenChart.setOption(getChartOption(dailyTokenTrend.value, 'Token', '#f56c6c'))
  }
  if (agentChartRef.value) {
    agentChart = echarts.init(agentChartRef.value)
    const data = Object.entries(agentDistribution.value).map(([name, value]) => ({ name, value }))
    agentChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 12 } },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 12 },
        data
      }]
    })
  }
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  messageChart?.resize()
  tokenChart?.resize()
  agentChart?.resize()
}

const loadStats = async () => {
  loading.value = true
  try {
    const response = await api.getConversationStats()
    if (response.status === 'success') {
      const d = response.data
      stats.value = d.summary || {}
      timeStats.value = d.time_stats || {}
      agentDistribution.value = d.agent_distribution || {}
      dailyTrend.value = d.daily_trend || []
      dailyTokenTrend.value = d.daily_token_trend || []
      await initCharts()
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

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  messageChart?.dispose()
  tokenChart?.dispose()
  agentChart?.dispose()
})
</script>

<style scoped>
.conversation-stats {
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

.time-stat {
  text-align: center;
  padding: 10px 0;
}

.time-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.time-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.chart-container {
  height: 250px;
}

.agent-dist {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-name {
  width: 80px;
  font-size: 13px;
  color: #606266;
}

.agent-count {
  width: 70px;
  font-size: 13px;
  color: #909399;
  text-align: right;
}

.agent-dist {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-name {
  width: 80px;
  font-size: 13px;
  color: #606266;
}

.agent-count {
  width: 70px;
  font-size: 13px;
  color: #909399;
  text-align: right;
}

.empty {
  text-align: center;
  color: #909399;
  padding: 30px 0;
}
</style>
