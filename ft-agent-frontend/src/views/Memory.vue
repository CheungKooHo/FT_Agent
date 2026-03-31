<template>
  <div class="memory-container">
    <div class="page-header">
      <el-button type="primary" @click="dialogVisible = true">
        <el-icon><Plus /></el-icon>
        添加记忆
      </el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="loadMemories">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="个人信息" name="fact" />
      <el-tab-pane label="偏好设置" name="preference" />
      <el-tab-pane label="习惯记录" name="habit" />
    </el-tabs>

    <div class="memory-list">
      <el-empty v-if="memories.length === 0" description="暂无记忆数据" />

      <el-card
        v-for="memory in memories"
        :key="memory.key"
        class="memory-card"
        shadow="hover"
      >
        <div class="memory-header">
          <el-tag :type="getMemoryTypeTag(memory.type)">
            {{ getMemoryTypeName(memory.type) }}
          </el-tag>
          <el-button
            type="danger"
            size="small"
            text
            @click="handleDelete(memory)"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>

        <div class="memory-content">
          <div class="memory-key">{{ memory.key }}</div>
          <div class="memory-value">{{ memory.value }}</div>
          <div v-if="memory.description" class="memory-description">
            {{ memory.description }}
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加记忆对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="添加记忆"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="记忆类型" prop="memory_type">
          <el-select v-model="form.memory_type" placeholder="请选择记忆类型">
            <el-option label="个人信息" value="fact" />
            <el-option label="偏好设置" value="preference" />
            <el-option label="习惯记录" value="habit" />
          </el-select>
        </el-form-item>

        <el-form-item label="记忆名称" prop="key">
          <el-input v-model="form.key" placeholder="例如：职业、喜好等" />
        </el-form-item>

        <el-form-item label="记忆内容" prop="value">
          <el-input
            v-model="form.value"
            type="textarea"
            :rows="3"
            placeholder="请输入记忆内容"
          />
        </el-form-item>

        <el-form-item label="备注说明" prop="description">
          <el-input
            v-model="form.description"
            placeholder="可选，对这条记忆的说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const userStore = useUserStore()

const activeTab = ref('all')
const memories = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const form = reactive({
  memory_type: 'fact',
  key: '',
  value: '',
  description: ''
})

const rules = {
  memory_type: [{ required: true, message: '请选择记忆类型', trigger: 'change' }],
  key: [{ required: true, message: '请输入记忆名称', trigger: 'blur' }],
  value: [{ required: true, message: '请输入记忆内容', trigger: 'blur' }]
}

// 获取记忆类型标签
const getMemoryTypeTag = (type) => {
  const typeMap = {
    fact: 'primary',
    preference: 'success',
    habit: 'warning'
  }
  return typeMap[type] || 'info'
}

// 获取记忆类型名称
const getMemoryTypeName = (type) => {
  const nameMap = {
    fact: '个人信息',
    preference: '偏好设置',
    habit: '习惯记录'
  }
  return nameMap[type] || type
}

// 加载记忆列表
const loadMemories = async () => {
  try {
    const memoryType = activeTab.value === 'all' ? null : activeTab.value
    const response = await api.getUserMemories(userStore.userInfo.user_id, memoryType)

    if (response.status === 'success') {
      memories.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载记忆失败')
  }
}

// 提交新记忆
const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.saveMemory({
          user_id: userStore.userInfo.user_id,
          ...form
        })

        ElMessage.success('添加成功')
        dialogVisible.value = false

        // 重置表单
        Object.keys(form).forEach(key => {
          form[key] = key === 'memory_type' ? 'fact' : ''
        })

        // 重新加载列表
        loadMemories()
      } catch (error) {
        ElMessage.error('添加失败')
      }
    }
  })
}

// 删除记忆
const handleDelete = async (memory) => {
  await ElMessageBox.confirm(`确定要删除记忆"${memory.key}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  try {
    await api.deleteMemory(userStore.userInfo.user_id, memory.key, memory.type)
    ElMessage.success('删除成功')
    loadMemories()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadMemories()
})
</script>

<style scoped>
.memory-container {
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

.memory-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.memory-card {
  margin-bottom: 12px;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.memory-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.memory-key {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.memory-value {
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.memory-description {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}

@media (min-width: 768px) {
  .memory-container {
    padding: 24px;
  }

  .page-header {
    margin-bottom: 24px;
  }

  .memory-list {
    padding: 20px 0;
  }

  .memory-card {
    margin-bottom: 16px;
  }

  .memory-header {
    margin-bottom: 12px;
  }

  .memory-content {
    gap: 8px;
  }

  .memory-key {
    font-size: 15px;
  }

  .memory-value {
    font-size: 14px;
    line-height: 1.6;
  }

  .memory-description {
    font-size: 13px;
  }
}
</style>
