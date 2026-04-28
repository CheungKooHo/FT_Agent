<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <el-tag :type="billingStore.subscription?.tier === 'pro' ? 'warning' : 'info'" size="small">
          {{ billingStore.subscription?.tier_name || '基础版' }}
        </el-tag>
        <span class="tier-hint" v-if="billingStore.subscription?.tier === 'basic'">
          <el-link type="primary" :underline="false" @click="$router.push('/billing')">升级专业版</el-link>
          解锁更多
        </span>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain size="small" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button type="danger" plain size="small" @click="handleClearChat">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div ref="messageListRef" class="message-list">
      <div v-if="messages.length === 0" class="empty-state">
        <el-icon :size="60" color="#dcdfe6"><ChatDotRound /></el-icon>
        <p>开始与财税专家对话</p>
        <p class="hint">输入您的问题，AI专家将为您解答</p>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-item"
        :class="msg.role"
      >
        <el-avatar v-if="msg.role === 'user'" :size="36" class="avatar">
          {{ userStore.userInfo?.nickname?.charAt(0) || '我' }}
        </el-avatar>
        <el-avatar v-else :size="36" class="avatar" :style="{ background: '#409EFF' }">
          <el-icon><Robot /></el-icon>
        </el-avatar>

        <div class="message-body">
          <div class="message-meta">
            <span class="sender">{{ msg.role === 'user' ? (userStore.userInfo?.nickname || '我') : '财税专家' }}</span>
            <span class="time">{{ msg.time }}</span>
          </div>
          <div class="message-text" :class="{ 'user-text': msg.role === 'user' }">
            <template v-if="msg.role === 'assistant' && !msg.streaming">
              <MarkdownContent :content="msg.content" />
            </template>
            <template v-else-if="msg.role === 'assistant' && msg.streaming">
              <span v-if="msg.content">{{ msg.content }}<span class="typing-cursor-inline"></span></span>
              <span v-else class="thinking-text">正在思考中<span class="thinking-dots"></span></span>
            </template>
            <span v-else>{{ msg.content }}</span>
          </div>

          <!-- 引用文献列表 -->
          <div v-if="msg.role === 'assistant' && msg.references && msg.references.length > 0" class="references-section">
            <div class="references-header">
              <span class="references-title">参考资料</span>
              <el-button type="primary" text size="small" @click="saveAllReferences(msg.references)">
                <el-icon><Download /></el-icon>
                全部保存
              </el-button>
            </div>
            <div
              v-for="(ref, idx) in msg.references"
              :key="idx"
              class="reference-item"
            >
              <span class="ref-index">{{ idx + 1 }}.</span>
              <span class="ref-source">{{ getRefSource(ref) }}</span>
              <el-button
                type="primary"
                text
                size="small"
                :loading="ref.saving"
                @click="saveReference(ref, msg.references)"
              >
                {{ ref.saved ? '已保存' : '保存' }}
              </el-button>
            </div>
          </div>

          <div class="message-actions">
            <el-button type="primary" text @click="copyMsg(msg.content)" class="copy-btn">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
            <el-button v-if="msg.role === 'assistant' && !msg.streaming && msg.showFeedback !== false" type="primary" text class="feedback-btn" @click="handleFeedback(msg, 'like')">
              <el-icon><Star /></el-icon>
              评价
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="isLoading && !messages.some(m => m.streaming)" class="message-item assistant">
        <el-avatar :size="36" class="avatar" :style="{ background: '#409EFF' }">
          <el-icon><Robot /></el-icon>
        </el-avatar>
        <div class="message-body">
          <div class="message-meta">
            <span class="sender">财税专家</span>
          </div>
          <div class="message-text loading">
            <span class="typing-cursor"></span>
            AI 思考中...
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入财税问题..."
        resize="none"
        @keydown.ctrl.enter="handleSend"
      />
      <div class="input-footer">
        <el-checkbox v-model="useMemory" size="small">启用记忆</el-checkbox>
        <el-button
          type="primary"
          :loading="isLoading"
          :disabled="!inputMessage.trim() || billingStore.tokenBalance <= 0"
          @click="handleSend"
        >
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
      </div>
    </div>

    <!-- 差评原因对话框 -->
    <el-dialog v-model="showFeedbackDialog" title="提交评价" width="400px">
      <el-form>
        <el-form-item label="差评原因">
          <el-select v-model="feedbackReason" placeholder="请选择原因" style="width: 100%;">
            <el-option v-for="r in feedbackReasons" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeedbackDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmFeedback">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onActivated, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useBillingStore } from '@/stores/billing'
import api from '@/api'
import MarkdownContent from '@/components/MarkdownContent.vue'

const userStore = useUserStore()
const billingStore = useBillingStore()

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const useMemory = ref(true)
const messageListRef = ref(null)

const soundEnabled = ref(localStorage.getItem('soundEnabled') !== 'false')
const autoSaveDraft = ref(localStorage.getItem('autoSaveDraft') === 'true')
const DRAFT_KEY = 'chat_draft'

let msgId = 0
const currentSessionId = ref('')

const copyMsg = async (content) => {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(content)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = content
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const showFeedbackDialog = ref(false)
const feedbackRating = ref('')
const feedbackReason = ref('')
const currentFeedbackMsg = ref(null)
const feedbackReasons = ['回答不准确', '回答不完整', '回答难以理解', '不符合政策规定', '其他']

const handleFeedback = async (msg, rating) => {
  if (!localStorage.getItem('token')) {
    ElMessage.warning('请先登录')
    return
  }
  currentFeedbackMsg.value = msg
  if (rating === 'dislike') {
    showFeedbackDialog.value = true
    feedbackRating.value = rating
  } else {
    // 直接提交好评
    await submitFeedback(msg, rating, '')
  }
}

const submitFeedback = async (msg, rating, reason) => {
  try {
    const sessionId = currentSessionId.value || 'default'
    await api.submitFeedback({
      session_id: sessionId,
      message_index: msg.id,
      rating,
      reason
    })
    ElMessage.success('感谢您的评价')
    msg.showFeedback = false
  } catch (error) {
    console.error('提交评价失败', error)
    ElMessage.error('评价提交失败，请重试')
  }
}

const confirmFeedback = async () => {
  if (!feedbackReason.value && feedbackRating.value === 'dislike') {
    ElMessage.warning('请选择或输入差评原因')
    return
  }
  await submitFeedback(currentFeedbackMsg.value, feedbackRating.value, feedbackReason.value)
  showFeedbackDialog.value = false
}

const playSound = () => {
  if (!soundEnabled.value) return
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = 800
    osc.type = 'sine'
    gain.gain.value = 0.1
    osc.start()
    setTimeout(() => osc.stop(), 100)
  } catch {}
}

const saveDraft = () => {
  if (autoSaveDraft.value && inputMessage.value.trim()) {
    localStorage.setItem(DRAFT_KEY, inputMessage.value)
  }
}

const loadDraft = () => {
  if (autoSaveDraft.value) {
    const draft = localStorage.getItem(DRAFT_KEY)
    if (draft) inputMessage.value = draft
  }
}

const clearDraft = () => localStorage.removeItem(DRAFT_KEY)

watch(inputMessage, saveDraft)

const formatTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

const scrollBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  if (billingStore.tokenBalance <= 0) {
    ElMessageBox.confirm('Token余额不足，请先充值', '余额不足', {
      confirmButtonText: '去充值',
      cancelButtonText: '取消'
    }).then(() => { window.location.href = '/billing' }).catch(() => {})
    return
  }

  const userMsg = {
    id: ++msgId,
    role: 'user',
    content: inputMessage.value.trim(),
    time: formatTime()
  }

  messages.value.push(userMsg)
  const userInput = inputMessage.value.trim()
  inputMessage.value = ''
  clearDraft()
  scrollBottom()

  // 创建 AI 消息占位（使用 reactive 确保响应式更新）
  const aiMsg = reactive({
    id: ++msgId,
    role: 'assistant',
    content: '',
    time: formatTime(),
    references: [],
    streaming: true  // 标记为流式进行中
  })
  messages.value.push(aiMsg)

  isLoading.value = true

  try {
    await api.chatStream({
      message: userInput,
      user_id: userStore.userInfo.user_id,
      use_memory: useMemory.value,
      conversation_history_limit: 10
    }, {
      onChunk: (chunk) => {
        aiMsg.content += chunk
        scrollBottom()
      },
      onFinish: (data) => {
        aiMsg.streaming = false
        aiMsg.references = data.references || []
        playSound()
        billingStore.fetchTokenBalance()
        scrollBottom()
      },
      onError: (error) => {
        aiMsg.streaming = false
        aiMsg.content = error || '发送失败'
        scrollBottom()
      }
    })
  } catch (err) {
    aiMsg.streaming = false
    aiMsg.content = err.message || '发送失败'
    scrollBottom()
  } finally {
    isLoading.value = false
  }
}

const handleExport = () => {
  if (messages.value.length === 0) {
    ElMessage.warning('暂无对话')
    return
  }
  let content = `对话导出 - ${new Date().toLocaleString('zh-CN')}\n${'='.repeat(50)}\n\n`
  messages.value.forEach(m => {
    content += `[${m.time}] ${m.role === 'user' ? '用户' : 'AI'}:\n${m.content}\n\n`
  })
  const blob = new Blob(['\ufeff' + content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `对话记录_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

const getRefSource = (ref) => {
  const source = ref.source || ''
  // 从完整路径中提取文件名
  if (source.includes('/')) {
    return source.split('/').pop()
  }
  return source || '未知来源'
}

const saveReference = async (ref, refs) => {
  if (ref.saved || ref.saving) return
  ref.saving = true
  try {
    const res = await api.saveReferenceDocument(ref.doc_id, ref.source, 'tax_basic')
    if (res.status === 'success') {
      ref.saved = true
      ElMessage.success(res.message || '已保存到知识库')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    ref.saving = false
  }
}

const saveAllReferences = async (refs) => {
  for (const ref of refs) {
    if (!ref.saved && !ref.saving) {
      await saveReference(ref, refs)
    }
  }
}

const handleClearChat = async () => {
  await ElMessageBox.confirm('确定清空当前对话？', '提示', { type: 'warning' })
  try {
    await api.clearConversationHistory(userStore.userInfo.user_id)
    messages.value = []
    ElMessage.success('已清空')
  } catch {
    ElMessage.error('清空失败')
  }
}

const loadHistory = async () => {
  try {
    const res = await api.getConversationHistory(userStore.userInfo.user_id, { limit: 50 })
    if (res.status === 'success' && res.data.length) {
      messages.value = res.data.map(m => ({
        id: ++msgId,
        role: m.role,
        content: m.content,
        references: m.references || [],
        time: m.time || formatTime()
      }))
      scrollBottom()
    }
  } catch {}
}

onMounted(async () => {
  await billingStore.init()
  loadHistory()
  loadDraft()
})

onActivated(() => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tier-hint {
  font-size: 12px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
}

.empty-state p {
  margin: 12px 0 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #c0c4cc;
}

.message-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
}

.message-body {
  max-width: 70%;
  min-width: 60px;
}

@media (max-width: 480px) {
  .message-item {
    position: relative;
    padding-left: 36px;
    padding-right: 0;
  }

  .message-item.user {
    padding-left: 0;
    padding-right: 36px;
  }

  .avatar {
    position: absolute;
    left: 0;
    top: 0;
    width: 28px !important;
    height: 28px !important;
  }

  .message-item.user .avatar {
    left: auto;
    right: 0;
  }

  .message-body {
    max-width: 100%;
  }

  .message-meta {
    font-size: 10px;
  }

  .message-text {
    padding: 8px 10px;
    font-size: 14px;
  }
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.message-item.user .message-meta {
  flex-direction: row-reverse;
}

.message-item.user .message-meta :deep(.el-button) {
  margin-left: 0;
  margin-right: 4px;
}

.sender {
  color: #606266;
  font-weight: 500;
}

.time {
  color: #c0c4cc;
}

.message-meta :deep(.el-button) {
  padding: 4px;
  margin-left: 4px;
}

.message-text {
  display: inline-block;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.message-actions {
  display: flex;
  margin-top: 4px;
}

.message-item.assistant .message-actions {
  justify-content: flex-start;
}

.message-item.user .message-actions {
  justify-content: flex-end;
}

.copy-btn {
  font-size: 12px;
  padding: 2px 8px;
  opacity: 0.5;
}

.copy-btn:hover {
  opacity: 1;
}

@media (max-width: 480px) {
  .copy-btn {
    opacity: 0.6;
  }
}

.message-item.assistant .message-text {
  background: #f5f7fa;
  color: #303133;
  border-radius: 4px 16px 16px 16px;
}

.message-item.user .message-text {
  background: #409eff;
  color: #fff;
  border-radius: 16px 4px 16px 16px;
}

.message-text.loading {
  color: #909399;
  display: flex;
  align-items: center;
  gap: 6px;
}

.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  background: #fff;
  flex-shrink: 0;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

@media (min-width: 768px) {
  .chat-header {
    padding: 16px 24px;
  }

  .message-list {
    padding: 20px 24px;
  }

  .chat-input {
    padding: 16px 24px;
  }
}

.references-section {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
}

.references-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.references-title {
  font-weight: 500;
  color: #606266;
}

.reference-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  color: #909399;
}

.ref-index {
  color: #409eff;
  font-weight: 500;
}

.ref-source {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #409EFF;
  animation: blink 1s infinite;
  margin-right: 4px;
  vertical-align: middle;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 流式消息中的光标 */
.message-item.assistant .message-text:not(.loading) .typing-cursor-inline {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #409EFF;
  animation: blink 1s infinite;
  margin-left: 2px;
  vertical-align: middle;
}

/* 正在思考中的文字 */
.thinking-text {
  color: #909399;
  font-style: italic;
}

.thinking-dots::after {
  content: '';
  animation: dots 1.5s infinite;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}
</style>