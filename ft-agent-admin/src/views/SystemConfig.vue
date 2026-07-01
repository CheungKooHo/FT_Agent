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
          <el-button type="primary" size="small" @click="saveItem('OPENAI_API_KEY', configForm.OPENAI_API_KEY)" :loading="savingKey">
            保存
          </el-button>
          <div class="form-tip">用于调用大模型 API，请从 <el-link type="primary" href="https://platform.deepseek.com" target="_blank">DeepSeek 平台</el-link> 获取</div>
        </el-form-item>

        <el-form-item label="API Base URL">
          <el-input
            v-model="configForm.OPENAI_API_BASE"
            placeholder="默认: https://api.deepseek.com"
            clearable
            style="max-width: 500px"
          />
          <el-button type="primary" size="small" @click="saveItem('OPENAI_API_BASE', configForm.OPENAI_API_BASE)" :loading="savingBase">
            保存
          </el-button>
          <div class="form-tip">如需使用其他 API 服务，可在此修改</div>
        </el-form-item>

        <el-form-item label="HuggingFace 镜像">
          <el-input
            v-model="configForm.HF_ENDPOINT"
            placeholder="默认: https://hf-mirror.com"
            clearable
            style="max-width: 500px"
          />
          <el-button type="primary" size="small" @click="saveItem('HF_ENDPOINT', configForm.HF_ENDPOINT)" :loading="savingHF">
            保存
          </el-button>
          <div class="form-tip">用于加速下载 HuggingFace 模型</div>
        </el-form-item>
      </el-form>

      <el-divider>功能配置</el-divider>

      <el-form :model="configForm" label-width="160px" class="config-form">
        <el-form-item label="专业版试用次数">
          <el-input-number
            v-model="configForm.trial_pro_count"
            :min="0"
            :max="99"
            style="max-width: 200px"
          />
          <el-button type="primary" size="small" @click="saveItem('trial_pro_count', configForm.trial_pro_count?.toString())" :loading="savingTrial">
            保存
          </el-button>
          <div class="form-tip">基础版用户每月可体验专业版的次数（0表示关闭试用）</div>
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
  HF_ENDPOINT: '',
  trial_pro_count: 3
})

const saving = ref(false)
const savingKey = ref(false)
const savingBase = ref(false)
const savingHF = ref(false)
const savingTrial = ref(false)

const saveItem = async (key, value) => {
  const loadingMap = {
    'OPENAI_API_KEY': savingKey,
    'OPENAI_API_BASE': savingBase,
    'HF_ENDPOINT': savingHF,
    'trial_pro_count': savingTrial
  }
  const loader = loadingMap[key]
  if (loader) loader.value = true
  try {
    await api.updateSystemConfig(key, value?.toString() || '')
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    if (loader) loader.value = false
  }
}

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
      configForm.value.trial_pro_count = parseInt(response.data.trial_pro_count) || 3
    }
  } catch (error) {
    console.error('加载配置失败:', error)
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
