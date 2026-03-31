<template>
  <div class="tokens">
    <el-card>
      <template #header>
        <span>Token 使用统计</span>
      </template>

      <el-table :data="topConsumers" stripe v-loading="loading">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="user_id" label="用户ID" width="200" show-overflow-tooltip />
        <el-table-column prop="total_consumed" label="累计消耗" width="120">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold;">{{ row.total_consumed }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_purchased" label="累计购买" width="120" />
        <el-table-column prop="balance" label="剩余余额" width="120">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: bold;">{{ row.balance }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const topConsumers = ref([])
const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const response = await api.getTokenStats()
    if (response.status === 'success') {
      topConsumers.value = response.data.top_consumers
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
</style>
