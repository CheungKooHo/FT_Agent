<template>
  <div class="users">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="版本">
          <el-select v-model="filterTier" placeholder="全部版本" clearable @change="handleFilter" style="width: 120px;">
            <el-option label="基础版" value="basic" />
            <el-option label="专业版" value="pro" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部状态" clearable @change="handleFilter" style="width: 120px;">
            <el-option label="正常" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="searchKeyword"
            placeholder="用户名/邮箱/昵称"
            clearable
            @clear="handleFilter"
            @keyup.enter="handleFilter"
            :prefix-icon="Search"
            style="width: 220px;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table :data="users" stripe v-loading="loading" @row-click="viewDetail" @sort-change="handleSortChange" class="user-table">
        <el-table-column prop="username" label="用户" min-width="8%">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="22" :icon="UserFilled" class="user-avatar" />
              <span class="username">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="10%">
          <template #default="{ row }">
            <span class="muted">{{ row.phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tier_name" label="版本" min-width="6%" align="center">
          <template #default="{ row }">
            <el-tag :type="row.tier === 'pro' ? 'warning' : 'info'" size="small" effect="light">
              {{ row.tier_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="token_balance" label="Token余额" min-width="8%" align="right" sortable>
          <template #default="{ row }">
            <span :class="['token-num', { 'low': row.token_balance < 100 }]">
              {{ formatNumber(row.token_balance) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_recharge_tokens" label="充值Token" min-width="8%" align="right" sortable>
          <template #default="{ row }">
            <span class="muted">{{ formatNumber(row.total_recharge_tokens) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_conversations" label="对话次数" min-width="7%" align="center" sortable>
          <template #default="{ row }">
            <span class="muted">{{ row.total_conversations || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="subscription_end" label="订阅到期" min-width="9%" sortable>
          <template #default="{ row }">
            <span v-if="row.subscription_end" :class="getExpireClass(row.subscription_end)">
              {{ formatExpireShort(row.subscription_end) }}
            </span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" min-width="9%" sortable>
          <template #default="{ row }">
            <span class="muted">{{ formatDateShort(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" min-width="8%" sortable>
          <template #default="{ row }">
            <span class="muted">{{ formatRelativeTime(row.last_login) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" min-width="5%" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small" effect="light">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="viewDetail(row)">详情</el-button>
            <el-button size="small" link @click.stop="toggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="warning" link @click.stop="grantToken(row)">赠送</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          @current-change="loadUsers"
          layout="total, prev, pager, next"
          background
        />
      </div>
    </el-card>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="用户详情" width="650px" destroy-on-close>
      <div class="detail-content" v-if="currentUser">
        <div class="detail-header">
          <el-avatar :size="64" :icon="UserFilled" />
          <div class="detail-title">
            <h3>{{ currentUser.username }}</h3>
            <el-tag :type="currentUser.tier === 'pro' ? 'warning' : 'info'" size="small">
              {{ currentUser.tier_name }}
            </el-tag>
            <el-tag :type="currentUser.is_active ? 'success' : 'danger'" size="small">
              {{ currentUser.is_active ? '正常' : '禁用' }}
            </el-tag>
          </div>
        </div>
        <el-divider />
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="用户ID" :span="2">
            <span class="mono">{{ currentUser.user_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="昵称">{{ currentUser.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ currentUser.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ currentUser.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Token余额">
            <span class="highlight">{{ formatNumber(currentUser.token_balance) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="累计消耗">
            <span class="highlight">{{ formatNumber(currentUser.token_total_consumed) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="充值Token">
            <span class="highlight">{{ formatNumber(currentUser.total_recharge_tokens) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="对话次数">
            <span class="highlight">{{ currentUser.total_conversations || 0 }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="上传文件">{{ currentUser.uploaded_files || 0 }} 个</el-descriptions-item>
          <el-descriptions-item label="订阅到期">
            <span v-if="currentUser.subscription_end" :class="getExpireClass(currentUser.subscription_end)">
              {{ formatExpire(currentUser.subscription_end) }}
            </span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(currentUser.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">{{ formatDate(currentUser.last_login) || '从未登录' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="warning" @click="grantToken(currentUser); detailDialogVisible = false">
          赠送Token
        </el-button>
        <el-button type="danger" @click="toggleStatus(currentUser); detailDialogVisible = false">
          {{ currentUser?.is_active ? '禁用用户' : '启用用户' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 赠送Token弹窗 -->
    <el-dialog v-model="grantDialogVisible" title="赠送Token" width="400px">
      <el-form label-width="80px">
        <el-form-item label="用户">
          <el-tag>{{ currentUser?.username }}</el-tag>
        </el-form-item>
        <el-form-item label="当前余额">
          {{ formatNumber(currentUser?.token_balance || 0) }}
        </el-form-item>
        <el-form-item label="赠送数量">
          <el-input-number v-model="grantAmount" :min="1" :max="100000" :step="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmGrantToken">确认赠送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, UserFilled } from '@element-plus/icons-vue'
import api from '@/api'

const users = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(15)
const total = ref(0)
const sortField = ref('created_at')
const sortOrder = ref('descending')

const filterTier = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')

const detailDialogVisible = ref(false)
const grantDialogVisible = ref(false)
const currentUser = ref(null)
const grantAmount = ref(100)

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

const formatRelativeTime = (dateStr) => {
  if (!dateStr) return '从未登录'
  const now = new Date()
  const date = new Date(dateStr)
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  return formatDate(dateStr)
}

const formatDateShort = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth()+1}/${d.getDate()}/${d.getFullYear()}`
}

const formatExpireShort = (dateStr) => {
  if (!dateStr) return '-'
  const now = new Date()
  const end = new Date(dateStr)
  const diff = end - now
  const days = Math.floor(diff / 86400000)

  if (diff < 0) return `已过期`
  if (days < 30) return `${days}天`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months}月`
  const years = Math.floor(months / 12)
  return `${years}年`
}

const formatExpire = (dateStr) => {
  if (!dateStr) return '-'
  const now = new Date()
  const end = new Date(dateStr)
  const diff = end - now
  const days = Math.floor(diff / 86400000)

  if (diff < 0) return `已过期`
  if (days === 0) return `今天到期`
  if (days === 1) return `明天到期`
  if (days < 30) return `${days}天后到期`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months}个月后到期`
  const years = Math.floor(months / 12)
  return `${years}年后到期`
}

const getExpireClass = (dateStr) => {
  if (!dateStr) return ''
  const now = new Date()
  const end = new Date(dateStr)
  const diff = end - now
  const days = Math.floor(diff / 86400000)

  if (diff < 0) return 'expired'
  if (days < 7) return 'expire-soon'
  if (days < 30) return 'expire-warning'
  return ''
}

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterTier.value) params.tier = filterTier.value
    if (filterStatus.value !== '') params.is_active = filterStatus.value
    if (searchKeyword.value) params.search = searchKeyword.value
    if (sortField.value) params.sort_field = sortField.value
    if (sortOrder.value === 'ascending') params.sort_order = 'asc'
    else params.sort_order = 'desc'

    const response = await api.getUsers(params.page, params.page_size, params)
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

const handleFilter = () => {
  currentPage.value = 1
  loadUsers()
}

const handleSortChange = ({ prop, order }) => {
  sortField.value = prop
  sortOrder.value = order
  loadUsers()
}

const resetFilter = () => {
  filterTier.value = ''
  filterStatus.value = ''
  searchKeyword.value = ''
  handleFilter()
}

const viewDetail = (user) => {
  currentUser.value = user
  detailDialogVisible.value = true
}

const toggleStatus = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`,
      '提示'
    )
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

.filter-card {
  margin-bottom: 15px;
}

.user-table {
  font-size: 14px;
}

.user-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

.user-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
  flex-shrink: 0;
}

.username {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.token-num {
  font-weight: 600;
  color: #303133;
  font-variant-numeric: tabular-nums;
}

.token-num.low {
  color: #f56c6c;
}

.muted {
  color: #909399;
  font-size: 13px;
}

.file-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 10px;
  font-size: 12px;
}

.expired {
  color: #f56c6c;
  font-weight: 500;
}

.expire-soon {
  color: #f56c6c;
}

.expire-warning {
  color: #e6a23c;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.detail-content {
  padding: 0 10px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 0;
}

.detail-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mono {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
}

.highlight {
  font-weight: 600;
  color: #409eff;
}
</style>
