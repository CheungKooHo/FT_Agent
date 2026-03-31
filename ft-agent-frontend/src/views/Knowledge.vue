<template>
  <div class="knowledge-container">
    <!-- 头部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <el-button type="primary" @click="uploadDialogVisible = true">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>
      </div>
      <div class="header-right">
        <el-button @click="testSearchDialogVisible = true" :disabled="files.length === 0">
          <el-icon><Search /></el-icon>
          测试检索
        </el-button>
        <el-button @click="loadFiles">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar" v-if="stats">
      <div class="stat-item">
        <span class="stat-value">{{ files.length }}</span>
        <span class="stat-label">文档数</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.collections?.tax_basic || 0 }}</span>
        <span class="stat-label">基础版切片</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.collections?.tax_pro || 0 }}</span>
        <span class="stat-label">专业版切片</span>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="files-list">
      <el-empty v-if="files.length === 0" description="暂无上传的文档">
        <el-button type="primary" @click="uploadDialogVisible = true">上传文档</el-button>
      </el-empty>

      <div v-else class="file-grid">
        <div
          v-for="file in files"
          :key="file.filename"
          class="file-card"
          :class="{ indexed: file.is_indexed, processing: !file.is_indexed }"
        >
          <div class="file-header">
            <el-icon :size="32" class="file-icon">
              <Document />
            </el-icon>
            <el-tag :type="file.is_indexed ? 'success' : 'warning'" size="small">
              {{ file.is_indexed ? '已索引' : '处理中' }}
            </el-tag>
          </div>

          <div class="file-info">
            <div class="file-name" :title="file.original_filename">
              {{ file.original_filename }}
            </div>
            <div class="file-meta">
              <span>{{ formatFileSize(file.size) }}</span>
              <span v-if="file.chunk_count"> {{ file.chunk_count }} 切片</span>
            </div>
            <div class="file-time">{{ formatDate(file.created_at) }}</div>
          </div>

          <div class="file-actions">
            <el-button type="primary" text size="small" @click="previewChunks(file)">
              预览
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(file)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文档到知识库"
      width="90%"
      max-width="340px"
    >
      <el-form label-width="80px">
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            accept=".pdf"
          >
            <el-button type="primary">选择PDF文件</el-button>
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

    <!-- 测试检索对话框 -->
    <el-dialog
      v-model="testSearchDialogVisible"
      title="测试知识库检索"
      width="90%"
      max-width="600px"
    >
      <el-input
        v-model="testQuery"
        type="textarea"
        :rows="2"
        placeholder="输入问题测试AI会检索到什么内容..."
      />
      <el-select v-model="testAgentType" style="margin-top: 12px; width: 100%">
        <el-option label="基础版知识库" value="tax_basic" />
        <el-option label="专业版知识库" value="tax_pro" />
      </el-select>

      <div v-if="searchPreview.length > 0" class="preview-results">
        <div class="preview-title">检索到 {{ searchPreview.length }} 条相关内容：</div>
        <div v-for="(chunk, idx) in searchPreview" :key="idx" class="preview-chunk">
          <div class="chunk-source">{{ chunk.source }} (切片{{ chunk.chunk_index + 1 }})</div>
          <div class="chunk-content">{{ chunk.content }}</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="testSearchDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="searching" :disabled="!testQuery.trim()" @click="handleTestSearch">
          搜索
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览片段对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="文档片段预览"
      width="90%"
      max-width="700px"
    >
      <div v-if="selectedFile" class="preview-info">
        <div class="preview-filename">{{ selectedFile.original_filename }}</div>
        <div class="preview-meta">
          {{ formatFileSize(selectedFile.size) }} |
          {{ selectedFile.chunk_count }} 切片 |
          {{ formatDate(selectedFile.created_at) }}
        </div>
      </div>

      <div v-if="previewChunksList.length > 0" class="chunks-list">
        <div v-for="(chunk, idx) in previewChunksList" :key="idx" class="chunk-item">
          <div class="chunk-header">切片 {{ idx + 1 }}</div>
          <div class="chunk-text">{{ chunk.content || '内容加载中...' }}</div>
        </div>
      </div>
      <el-empty v-else description="该文档暂无切片或尚未索引" />

      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBillingStore } from '@/stores/billing'
import api from '@/api'

const billingStore = useBillingStore()

const files = ref([])
const stats = ref(null)
const uploadDialogVisible = ref(false)
const testSearchDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const uploading = ref(false)
const searching = ref(false)
const uploadProgress = ref(0)
const uploadRef = ref(null)
const testQuery = ref('')
const testAgentType = ref('tax_basic')
const searchPreview = ref([])
const selectedFile = ref(null)
const previewChunksList = ref([])

const uploadForm = ref({
  file: null
})

const agentType = () => {
  return billingStore.subscription?.tier === 'pro' ? 'tax_pro' : 'tax_basic'
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}

const loadFiles = async () => {
  try {
    const response = await api.getKnowledgeFiles()
    if (response.status === 'success') {
      files.value = response.files || []
      stats.value = { collections: response.collections }
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
    ElMessage.error('加载文件列表失败')
  }
}

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
      agentType(),
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

const handleTestSearch = async () => {
  if (!testQuery.value.trim()) return

  searching.value = true
  try {
    const response = await api.searchKnowledgePreview(
      testQuery.value,
      testAgentType.value,
      5
    )
    if (response.status === 'success') {
      searchPreview.value = response.chunks || []
    }
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const previewChunks = async (file) => {
  selectedFile.value = file
  previewDialogVisible.value = true

  // 简单模拟：实际应该从后端获取该文档的切片
  // 这里用搜索结果代替
  if (file.is_indexed) {
    try {
      const response = await api.searchKnowledgePreview(
        file.original_filename,
        file.agent_type || 'tax_basic',
        file.chunk_count || 3
      )
      if (response.status === 'success') {
        previewChunksList.value = response.chunks || []
      }
    } catch {
      previewChunksList.value = []
    }
  } else {
    previewChunksList.value = []
  }
}

const handleDelete = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${file.original_filename}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )

    const response = await api.deleteKnowledgeFile(file.filename)
    if (response.status === 'success') {
      ElMessage.success('文件已删除')
      loadFiles()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
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
  padding: 12px;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  gap: 8px;
}

.stats-bar {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

.files-list {
  flex: 1;
  overflow-y: auto;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.file-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

.file-card.indexed {
  border-color: #67c23a;
}

.file-card.processing {
  border-color: #e6a23c;
  opacity: 0.7;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.file-icon {
  color: #f56c6c;
}

.file-info {
  margin-bottom: 8px;
}

.file-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.file-meta {
  font-size: 11px;
  color: #909399;
}

.file-time {
  font-size: 10px;
  color: #c0c4cc;
  margin-top: 2px;
}

.file-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid #f5f7fa;
}

.preview-results {
  margin-top: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.preview-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.preview-chunk {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}

.chunk-source {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.chunk-content {
  font-size: 12px;
  color: #303133;
  line-height: 1.5;
  max-height: 80px;
  overflow: hidden;
}

.preview-info {
  margin-bottom: 16px;
}

.preview-filename {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.preview-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.chunks-list {
  max-height: 400px;
  overflow-y: auto;
}

.chunk-item {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.chunk-header {
  font-size: 11px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 6px;
}

.chunk-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

@media (min-width: 768px) {
  .knowledge-container {
    padding: 20px 24px;
  }

  .page-header {
    margin-bottom: 20px;
  }

  .stats-bar {
    padding: 16px;
    gap: 32px;
    margin-bottom: 20px;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 13px;
  }

  .file-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }

  .file-card {
    padding: 16px;
  }

  .file-name {
    font-size: 14px;
  }
}
</style>
