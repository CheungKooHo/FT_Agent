<template>
  <div class="users">
    <el-card>
      <template #header>
        <span>用户管理</span>
      </template>

      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="tier_name" label="版本" width="100">
          <template #default="{ row }">
            <el-tag :type="row.tier === 'pro' ? 'warning' : 'info'" size="small">
              {{ row.tier_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="token_balance" label="Token余额" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="toggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="primary" @click="grantToken(row)">
              赠送Token
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @current-change="loadUsers"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>

    <el-dialog v-model="grantDialogVisible" title="赠送Token" width="400px">
      <el-form>
        <el-form-item label="用户">
          <span>{{ currentUser?.username }}</span>
        </el-form-item>
        <el-form-item label="赠送数量">
          <el-input-number v-model="grantAmount" :min="1" :max="100000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmGrantToken">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const users = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const grantDialogVisible = ref(false)
const currentUser = ref(null)
const grantAmount = ref(100)

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await api.getUsers(currentPage.value, pageSize.value)
    if (response.status === 'success') {
      users.value = response.data.users
      total.value = response.data.total
    }
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const toggleStatus = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`, '提示')
    await api.toggleUserStatus(user.user_id)
    ElMessage.success('操作成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const grantToken = (user) => {
  currentUser.value = user
  grantAmount.value = 100
  grantDialogVisible.value = true
}

const confirmGrantToken = async () => {
  try {
    await api.grantToken(currentUser.value.user_id, grantAmount.value)
    ElMessage.success('赠送成功')
    grantDialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error('赠送失败')
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users {
  padding: 0;
}
</style>
