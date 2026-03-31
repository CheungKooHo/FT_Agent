<template>
  <div class="tiers-container">
    <div class="header">
      <h2>订阅版本管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建版本
      </el-button>
    </div>

    <el-table :data="tiers" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="tier_code" label="版本代码" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.tier_code }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tier_name" label="版本名称" width="120" />
      <el-table-column prop="agent_type" label="关联Agent" width="120">
        <template #default="{ row }">
          <el-tag type="info">{{ row.agent_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="monthly_token_quota" label="每月Token" width="100" />
      <el-table-column prop="price_monthly" label="月费(分)" width="100">
        <template #default="{ row }">
          {{ row.price_monthly === 0 ? '免费' : (row.price_monthly / 100).toFixed(0) + '元' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑版本' : '新建版本'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版本代码" required>
          <el-input v-model="form.tier_code" :disabled="isEdit" placeholder="如: basic, pro" />
        </el-form-item>
        <el-form-item label="版本名称" required>
          <el-input v-model="form.tier_name" placeholder="如: 基础版, 专业版" />
        </el-form-item>
        <el-form-item label="关联Agent" required>
          <el-select v-model="form.agent_type" placeholder="选择关联的Agent">
            <el-option v-for="agent in agents" :key="agent.id" :label="`${agent.name} (${agent.agent_type})`" :value="agent.agent_type" />
          </el-select>
        </el-form-item>
        <el-form-item label="每月Token" required>
          <el-input-number v-model="form.monthly_token_quota" :min="0" />
        </el-form-item>
        <el-form-item label="月费(元)" required>
          <el-input-number v-model="form.price_monthly_yuan" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="版本描述..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const tiers = ref([])
const agents = ref([])
const showDialog = ref(false)
const isEdit = ref(false)

const form = ref({
  id: null,
  tier_code: '',
  tier_name: '',
  agent_type: '',
  monthly_token_quota: 1000,
  price_monthly_yuan: 0,
  is_active: true,
  description: ''
})

const loadTiers = async () => {
  loading.value = true
  try {
    const response = await api.getTiers()
    if (response.status === 'success') {
      tiers.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载订阅版本失败')
  } finally {
    loading.value = false
  }
}

const loadAgents = async () => {
  try {
    const response = await api.getAgents()
    if (response.status === 'success') {
      agents.value = response.data.filter(a => a.is_active)
    }
  } catch (error) {
    // ignore
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  form.value = {
    id: null,
    tier_code: '',
    tier_name: '',
    agent_type: '',
    monthly_token_quota: 1000,
    price_monthly_yuan: 0,
    is_active: true,
    description: ''
  }
  showDialog.value = true
}

const openEditDialog = (tier) => {
  isEdit.value = true
  form.value = {
    ...tier,
    price_monthly_yuan: tier.price_monthly === 0 ? 0 : tier.price_monthly / 100
  }
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!form.value.tier_code || !form.value.tier_name || !form.value.agent_type) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    const price_monthly = Math.round(form.value.price_monthly_yuan * 100)
    const data = {
      ...form.value,
      price_monthly
    }
    delete data.price_monthly_yuan

    if (isEdit.value) {
      await api.updateTier(form.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await api.createTier(data)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadTiers()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (tier) => {
  try {
    await ElMessageBox.confirm(`确定删除版本「${tier.tier_name}」？`, '删除确认', { type: 'warning' })
    await api.deleteTier(tier.id)
    ElMessage.success('删除成功')
    loadTiers()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => { loadTiers(); loadAgents() })
</script>

<style scoped>
.tiers-container { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header h2 { margin: 0; }
</style>