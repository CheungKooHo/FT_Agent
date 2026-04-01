<template>
  <div class="policies">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>政策文档管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加文档
          </el-button>
        </div>
      </template>

      <el-form inline>
        <el-form-item label="分类">
          <el-select v-model="category" placeholder="全部" clearable @change="loadPolicies" style="width: 120px;">
            <el-option label="税务" value="tax" />
            <el-option label="财务" value="finance" />
            <el-option label="审计" value="audit" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="policies" stripe v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="document_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ getTypeName(row.document_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="editPolicy(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deletePolicy(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @current-change="loadPolicies"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑文档' : '添加文档'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%;">
            <el-option label="税务" value="tax" />
            <el-option label="财务" value="finance" />
            <el-option label="审计" value="audit" />
          </el-select>
        </el-form-item>
        <el-form-item label="文档类型">
          <el-select v-model="form.document_type" placeholder="请选择类型" style="width: 100%;">
            <el-option label="国家级" value="national" />
            <el-option label="省级" value="provincial" />
            <el-option label="地方级" value="local" />
            <el-option label="行业" value="industry" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源URL">
          <el-input v-model="form.source_url" placeholder="请输入来源链接" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPolicy">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { Plus } from '@element-plus/icons-vue'

const policies = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const category = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const currentPolicyId = ref(null)

const form = reactive({
  title: '',
  category: 'tax',
  document_type: 'national',
  source_url: ''
})

const getCategoryName = (cat) => {
  const map = { tax: '税务', finance: '财务', audit: '审计' }
  return map[cat] || cat
}

const getTypeName = (type) => {
  const map = { national: '国家级', provincial: '省级', local: '地方级', industry: '行业' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadPolicies = async () => {
  loading.value = true
  try {
    const response = await api.getPolicyDocuments(
      currentPage.value,
      pageSize.value,
      category.value || null
    )
    if (response.status === 'success') {
      policies.value = response.data.documents
      total.value = response.data.total
    }
  } catch (error) {
    ElMessage.error('加载政策列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  currentPolicyId.value = null
  Object.assign(form, {
    title: '',
    category: 'tax',
    document_type: 'national',
    source_url: ''
  })
  dialogVisible.value = true
}

const editPolicy = (policy) => {
  isEdit.value = true
  currentPolicyId.value = policy.id
  Object.assign(form, {
    title: policy.title,
    category: policy.category,
    document_type: policy.document_type,
    source_url: policy.source_url || ''
  })
  dialogVisible.value = true
}

const submitPolicy = async () => {
  if (!form.title || !form.category) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    if (isEdit.value) {
      await api.updatePolicyDocument(currentPolicyId.value, form)
      ElMessage.success('更新成功')
    } else {
      await api.createPolicyDocument(form)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadPolicies()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deletePolicy = async (policy) => {
  try {
    await ElMessageBox.confirm(`确定删除文档 "${policy.title}" 吗？`, '提示')
    await api.deletePolicyDocument(policy.id)
    ElMessage.success('删除成功')
    loadPolicies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadPolicies()
})
</script>

<style scoped>
.policies {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
