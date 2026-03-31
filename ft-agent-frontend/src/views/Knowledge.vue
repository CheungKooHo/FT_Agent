<template>
  <div class="knowledge-container">
    <div class="page-header">
      <el-button type="primary" @click="uploadDialogVisible = true">
        <el-icon><Upload /></el-icon>
        上传文档
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form inline>
        <el-form-item>
          <el-button type="primary" @click="loadFiles">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="files-list">
      <el-empty v-if="files.length === 0" description="暂无上传的文档" />

      <el-row :gutter="16" v-else>
        <el-col
          v-for="file in files"
          :key="file.filename"
          :span="8"
          style="margin-bottom: 16px"
        >
          <el-card class="file-card" shadow="hover">
            <div class="file-icon">
              <el-icon :size="48" color="#F56C6C"><Document /></el-icon>
            </div>
            <div class="file-info">
              <div class="file-name" :title="file.filename">
                {{ file.filename }}
              </div>
              <div class="file-meta">
                <div>大小: {{ formatFileSize(file.size) }}</div>
                <div>上传时间: {{ formatDate(file.created_at) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文档到知识库"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            accept=".pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 PDF 文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="uploadProgress > 0">
          <el-progress :percentage="uploadProgress" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!uploadForm.file"
          @click="handleUpload"
        >
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useBillingStore } from '@/stores/billing'
import api from '@/api'

const billingStore = useBillingStore()
const files = ref([])
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadRef = ref(null)

const uploadForm = ref({
  file: null
})

// 根据订阅等级获取 agent_type
const agentType = computed(() => {
  const tier = billingStore.subscription?.tier
  return tier === 'pro' ? 'tax_pro' : 'tax_basic'
})

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 文件选择
const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}

// 加载文件列表
const loadFiles = async () => {
  try {
    const response = await api.getUploadedFiles()
    if (response.status === 'success') {
      files.value = response.files
    }
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

// 上传文件
const handleUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0

  try {
    const response = await api.uploadFile(
      uploadForm.value.file,
      agentType.value,
      (percent) => {
        uploadProgress.value = percent
      }
    )

    if (response.status === 'success') {
      ElMessage.success('上传成功！文档正在处理中...')
      uploadDialogVisible.value = false

      uploadForm.value.file = null
      uploadProgress.value = 0
      uploadRef.value?.clearFiles()

      loadFiles()
    }
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  await billingStore.init()
  loadFiles()
})
</script>

<style scoped>
.knowledge-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  padding: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.filter-card {
  margin-bottom: 16px;
}

.files-list {
  flex: 1;
  overflow-y: auto;
}

.file-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.file-card:hover {
  transform: translateY(-4px);
}

.file-icon {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.file-info {
  text-align: center;
}

.file-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.file-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

@media (min-width: 768px) {
  .knowledge-container {
    padding: 24px;
  }

  .page-header {
    margin-bottom: 24px;
  }

  .filter-card {
    margin-bottom: 24px;
  }

  .file-icon {
    padding: 20px 0;
  }

  .file-name {
    margin-bottom: 12px;
    font-size: 14px;
  }

  .file-meta {
    font-size: 13px;
  }
}
</style>