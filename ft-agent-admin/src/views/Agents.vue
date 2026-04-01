<template>
  <div class="agents-container">
    <div class="header">
      <h2>Agent 配置管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建 Agent
      </el-button>
    </div>

    <el-table :data="agents" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="agent_type" label="版本标识" width="150">
        <template #default="{ row }">
          <el-tag>{{ row.agent_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="model" label="模型" width="120" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="prompt" label="System Prompt">
        <template #default="{ row }">
          <el-tooltip :content="row.prompt" placement="top" :disabled="!row.prompt">
            <span class="prompt-preview">{{ row.prompt?.substring(0, 100) }}{{ row.prompt?.length > 100 ? '...' : '' }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑 Agent' : '新建 Agent'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版本标识" required>
          <el-input v-model="form.agent_type" :disabled="isEdit" placeholder="如: tax_standard, tax_pro, pet_pro" />
          <div class="form-tip">唯一标识，如 tax_standard 表示标准版，tax_pro 表示专业版</div>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如: 财税专家-标准版" />
        </el-form-item>
        <el-form-item label="模型" required>
          <el-select v-model="form.model" placeholder="选择模型" style="width: 100%;">
            <el-option label="DeepSeek Chat" value="deepseek-chat" />
            <el-option label="DeepSeek Coder" value="deepseek-coder" />
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-3.5" value="gpt-3.5-turbo" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="System Prompt" required>
          <el-input v-model="form.prompt" type="textarea" :rows="8" placeholder="输入 AI Agent 的系统提示词..." />
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
const agents = ref([])
const showDialog = ref(false)
const isEdit = ref(false)

const form = ref({
  id: null,
  agent_type: '',
  name: '',
  model: 'deepseek-chat',
  prompt: '',
  is_active: true
})

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await api.getAgents()
    if (response.status === 'success') {
      agents.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  form.value = { id: null, agent_type: '', name: '', model: 'deepseek-chat', prompt: '', is_active: true }
  showDialog.value = true
}

const openEditDialog = (agent) => {
  isEdit.value = true
  form.value = { ...agent }
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!form.value.agent_type || !form.value.name || !form.value.prompt) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.updateAgent(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.createAgent(form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadAgents()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (agent) => {
  try {
    await ElMessageBox.confirm(`确定删除 Agent「${agent.name}」？`, '删除确认', { type: 'warning' })
    await api.deleteAgent(agent.id)
    ElMessage.success('删除成功')
    loadAgents()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => { loadAgents() })
</script>

<style scoped>
.agents-container { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header h2 { margin: 0; }
.prompt-preview {
  display: inline-block;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}
</style>