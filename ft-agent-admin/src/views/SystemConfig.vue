<template>
  <div class="system-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统配置</span>
        </div>
      </template>

      <el-form :model="configForm" label-width="140px" class="config-form">
        <el-form-item label="DeepSeek API Key">
          <el-input
            v-model="configForm.OPENAI_API_KEY"
            type="password"
            placeholder="请输入 DeepSeek API Key"
            show-password
            clearable
            style="max-width: 500px"
          />
          <div class="form-tip">用于调用大模型 API，请从 <el-link type="primary" href="https://platform.deepseek.com" target="_blank">DeepSeek 平台</el-link> 获取</div>
        </el-form-item>

        <el-form-item label="API Base URL">
          <el-input
            v-model="configForm.OPENAI_API_BASE"
            placeholder="默认: https://api.deepseek.com"
            clearable
            style="max-width: 500px"
          />
          <div class="form-tip">如需使用其他 API 服务，可在此修改</div>
        </el-form-item>

        <el-form-item label="HuggingFace 镜像">
          <el-input
            v-model="configForm.HF_ENDPOINT"
            placeholder="默认: https://hf-mirror.com"
            clearable
            style="max-width: 500px"
          />
          <div class="form-tip">用于加速下载 HuggingFace 模型</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveConfigs" :loading="saving">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>环境变量参考</span>
        </div>
      </template>
      <div class="env-table">
        <el-table :data="envVars" border size="small">
          <el-table-column prop="key" label="变量名" width="200" />
          <el-table-column prop="description" label="说明" />
          <el-table-column prop="default" label="默认值" width="200" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const configForm = ref({
  OPENAI_API_KEY: '',
  OPENAI_API_BASE: '',
  HF_ENDPOINT: ''
})

const saving = ref(false)

const envVars = [
  { key: 'OPENAI_API_KEY', description: 'DeepSeek API Key（必填）', default: '-' },
  { key: 'OPENAI_API_BASE', description: 'API 地址', default: 'https://api.deepseek.com' },
  { key: 'HF_ENDPOINT', description: 'HuggingFace 镜像', default: 'https://hf-mirror.com' },
  { key: 'DB_PASSWORD', description: '数据库密码', default: '-' }
]

const loadConfigs = async () => {
  try {
    const response = await api.getSystemConfigs()
    if (response.status === 'success' && response.data) {
      configForm.value.OPENAI_API_KEY = response.data.OPENAI_API_KEY || ''
      configForm.value.OPENAI_API_BASE = response.data.OPENAI_API_BASE || ''
      configForm.value.HF_ENDPOINT = response.data.HF_ENDPOINT || ''
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const saveConfigs = async () => {
  saving.value = true
  try {
    const keys = ['OPENAI_API_KEY', 'OPENAI_API_BASE', 'HF_ENDPOINT']
    for (const key of keys) {
      await api.updateSystemConfig(key, configForm.value[key] || '')
    }
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.system-config {
  max-width: 800px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-form {
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.env-table {
  margin-top: 10px;
}
</style>
