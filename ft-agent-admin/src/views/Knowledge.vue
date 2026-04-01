<template>
  <div class="knowledge">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_files || 0 }}</div>
            <div class="stat-label">文件总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.indexed_files || 0 }}</div>
            <div class="stat-label">已索引</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ formatSize(stats.total_size_bytes) }}</div>
            <div class="stat-label">总大小</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.collections?.tax_basic?.vectors_count || 0 }}</div>
            <div class="stat-label">Tax Basic 向量数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>RAG 知识库管理</span>
          <el-button type="primary" @click="showUploadDialog">
            <el-icon><Plus /></el-icon>
            上传文档
          </el-button>
        </div>
      </template>

      <!-- 过滤条件 -->
      <el-form inline style="margin-bottom: 15px;">
        <el-form-item label="Agent 类型">
          <el-select v-model="agentType" placeholder="全部" clearable @change="loadFiles" style="width: 140px;">
            <el-option label="税务基础版" value="tax_basic" />
            <el-option label="税务专业版" value="tax_pro" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadStats">刷新统计</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="files" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="上传用户" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.user_id === 'admin' ? 'danger' : 'info'">
              {{ row.username || row.user_id }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="original_filename" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="agent_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getAgentTypeName(row.agent_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="切片数" width="80" />
        <el-table-column prop="is_indexed" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_indexed ? 'success' : 'warning'" size="small">
              {{ row.is_indexed ? '已索引' : '未索引' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="previewFile(row)">预览</el-button>
            <el-button size="small" type="danger" link @click="deleteFile(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @current-change="loadFiles"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档到知识库" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="Agent 类型" required>
          <el-select v-model="uploadForm.agentType" placeholder="请选择类型" style="width: 100%;">
            <el-option label="税务基础版" value="tax_basic" />
            <el-option label="税务专业版" value="tax_pro" />
          </el-select>
        </el-form-item>
        <el-form-item label="PDF 文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".pdf"
            :on-change="handleFileChange"
          >
            <el-button type="primary">选择 PDF 文件</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传 PDF 文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="文档内容预览" width="80%" max-width="900px" destroy-on-close>
      <div v-if="previewLoading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      <div v-else-if="previewChunks.length === 0" style="text-align: center; padding: 40px; color: #909399;">
        暂无索引内容
      </div>
      <div v-else class="chunks-container">
        <div class="chunk-item" v-for="(chunk, index) in previewChunks" :key="index">
          <div class="chunk-header">
            <span class="chunk-index">#{{ chunk.chunk_index + 1 }}</span>
            <span class="chunk-source">{{ chunk.source }}</span>
          </div>
          <div class="chunk-content">{{ chunk.content }}</div>
        </div>
      </div>
      <template #footer v-if="previewChunks.length > 0">
        <div class="preview-footer">
          <span class="chunk-count">共 {{ previewChunks.length }} 个切片</span>
          <el-button @click="previewDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { Plus, Loading } from '@element-plus/icons-vue'

const files = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const agentType = ref('')

const stats = ref({})
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)
const uploadForm = reactive({
  agentType: 'tax_basic',
  file: null
})

const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewChunks = ref([])
const previewFileName = ref('')

const getAgentTypeName = (type) => {
  const map = { tax_basic: '税务基础版', tax_pro: '税务专业版' }
  return map[type] || type || '未知'
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadFiles = async () => {
  loading.value = true
  try {
    const response = await api.getKnowledgeFiles(
      currentPage.value,
      pageSize.value,
      agentType.value || null
    )
    if (response.status === 'success') {
      files.value = response.data.files
      total.value = response.data.total
    }
  } catch (error) {
    ElMessage.error('加载知识库文件失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await api.getKnowledgeStats()
    if (response.status === 'success') {
      stats.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载统计信息失败')
  }
}

const showUploadDialog = () => {
  uploadForm.agentType = 'tax_basic'
  uploadForm.file = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  uploadDialogVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const submitUpload = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请选择 PDF 文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('agent_type', uploadForm.agentType)

    await api.uploadKnowledgeFile(formData)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    loadFiles()
    loadStats()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const previewFile = async (file) => {
  previewFileName.value = file.original_filename
  previewChunks.value = []
  previewDialogVisible.value = true
  previewLoading.value = true
  try {
    const response = await api.getFileChunks(file.filename)
    if (response.status === 'success') {
      previewChunks.value = response.chunks || []
    } else {
      ElMessage.error(response.message || '加载预览失败')
    }
  } catch (error) {
    ElMessage.error('加载预览失败')
  } finally {
    previewLoading.value = false
  }
}

const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定删除文件 "${file.original_filename}" 吗？`, '提示')
    await api.deleteKnowledgeFile(file.filename)
    ElMessage.success('删除成功')
    loadFiles()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadFiles()
  loadStats()
})
</script>

<style scoped>
.knowledge {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.chunks-container {
  max-height: 500px;
  overflow-y: auto;
}

.chunk-item {
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.chunk-item:last-child {
  margin-bottom: 0;
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f5f7fa;
}

.chunk-index {
  background: #409eff;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.chunk-source {
  color: #909399;
  font-size: 12px;
}

.chunk-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chunk-count {
  color: #909399;
  font-size: 13px;
}
</style>
