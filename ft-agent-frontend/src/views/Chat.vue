<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <el-tag
          :type="billingStore.subscription?.tier === 'pro' ? 'warning' : 'info'"
          size="small"
        >
          {{ billingStore.subscription?.tier_name || "基础版" }}
        </el-tag>
        <span
          class="tier-hint"
          v-if="billingStore.subscription?.tier === 'basic'"
        >
          <el-link
            type="primary"
            :underline="false"
            @click="$router.push('/billing')"
            >升级专业版</el-link
          >
          解锁专业分析、计算、方案建议
        </span>
      </div>
    </div>

    <div ref="messageListRef" class="message-list">
      <div v-if="messages.length === 0" class="empty-state">
        <el-icon :size="60" color="#dcdfe6"><ChatDotRound /></el-icon>
        <p>
          开始与{{
            billingStore.subscription?.tier === "pro"
              ? "财税专家-专业版"
              : "财税专家-基础版"
          }}对话
        </p>
        <p class="hint">基础版可答政策，专业版更可分析方案</p>
        <!-- 推荐问题 -->
        <div class="recommended-questions">
          <p class="rq-title">试试这样问:</p>
          <div class="rq-list">
            <el-tag
              v-for="q in recommendedQuestions"
              :key="q"
              type="info"
              class="rq-tag"
              @click="fillQuestion(q)"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-item"
        :class="msg.role"
      >
        <div class="message-role">
          <el-avatar v-if="msg.role === 'user'" :size="36" class="avatar">
            {{ userStore.userInfo?.nickname?.charAt(0) || "我" }}
          </el-avatar>
          <el-avatar
            v-else
            :size="36"
            class="avatar"
            :style="{
              background:
                (msg.agentType || billingStore.subscription?.tier) === 'pro'
                  ? '#E6A23C'
                  : '#409EFF',
            }"
          >
            <svg viewBox="0 0 24 24" width="24" height="24" fill="#fff">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
              />
            </svg>
          </el-avatar>
          <div class="message-meta">
            <div class="sender">
              {{
                msg.role === "user"
                  ? userStore.userInfo?.nickname || "我"
                  : (msg.agentType || billingStore.subscription?.tier) === "pro"
                  ? "财税专家-专业版"
                  : "财税专家-基础版"
              }}
            </div>
            <div class="time">{{ msg.time }}</div>
          </div>
        </div>

        <div class="message-body">
          <div
            class="message-text"
            :class="{ 'user-text': msg.role === 'user' }"
          >
            <template v-if="msg.role === 'assistant' && !msg.streaming">
              <MarkdownContent :content="msg.content" />
            </template>
            <template v-else-if="msg.role === 'assistant' && msg.streaming">
              <span v-if="msg.content"
                >{{ msg.content }}<span class="typing-cursor-inline"></span
              ></span>
              <span v-else class="thinking-text"
                >正在思考中<span class="thinking-dots"></span
              ></span>
            </template>
            <span v-else>{{ msg.content }}</span>
          </div>

          <!-- 引用文献列表 -->
          <div
            v-if="
              msg.role === 'assistant' &&
              msg.references &&
              msg.references.length > 0
            "
            class="references-section"
          >
            <div class="references-header">
              <span class="references-title">参考资料</span>
              <el-button
                type="primary"
                text
                size="small"
                @click="saveAllReferences(msg.references)"
              >
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
                {{ ref.saved ? "已保存" : "保存" }}
              </el-button>
            </div>
          </div>

          <div class="message-actions">
            <el-button
              type="primary"
              text
              @click="copyMsg(msg.content)"
              class="copy-btn"
            >
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
            <el-button
              type="warning"
              text
              class="copy-btn"
              @click="toggleFavorite(msg)"
              :title="isFavorited(msg) ? '取消收藏' : '收藏'"
            >
              <el-icon><Star /></el-icon>
              {{ isFavorited(msg) ? "已收藏" : "收藏" }}
            </el-button>
            <template
              v-if="
                msg.role === 'assistant' &&
                !msg.streaming &&
                msg.showFeedback !== false
              "
            >
              <el-button
                type="success"
                text
                class="feedback-btn"
                @click="handleFeedback(msg, 'like')"
                title="好评"
              >
                👍
              </el-button>
              <el-button
                type="danger"
                text
                class="feedback-btn"
                @click="handleFeedback(msg, 'dislike')"
                title="差评"
              >
                👎
              </el-button>
            </template>
          </div>
          <!-- 内联差评原因选择 -->
          <div v-if="msg.showDislikeReason" class="dislike-reason-inline">
            <el-select
              v-model="feedbackReason"
              placeholder="请选择原因"
              size="small"
              style="width: 160px"
            >
              <el-option
                v-for="r in feedbackReasons"
                :key="r"
                :label="r"
                :value="r"
              />
            </el-select>
            <el-button
              size="small"
              type="primary"
              @click="confirmInlineDislike(msg)"
              >提交</el-button
            >
            <el-button size="small" @click="msg.showDislikeReason = false"
              >取消</el-button
            >
          </div>
        </div>
      </div>

      <div
        v-if="isLoading && !messages.some((m) => m.streaming)"
        class="message-item assistant"
      >
        <div class="message-role">
          <el-avatar
            :size="36"
            class="avatar"
            :style="{
              background:
                billingStore.subscription?.tier === 'pro'
                  ? '#E6A23C'
                  : '#409EFF',
            }"
          >
            <svg viewBox="0 0 24 24" width="24" height="24" fill="#fff">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
              />
            </svg>
          </el-avatar>
          <div class="message-meta">
            <span class="sender">{{
              billingStore.subscription?.tier === "pro"
                ? "财税专家-专业版"
                : "财税专家-基础版"
            }}</span>
          </div>
        </div>
        <div class="message-body">
          <div class="message-text loading">
            <span class="typing-cursor"></span>
            AI 思考中...
          </div>
        </div>
      </div>

      <!-- 对话后的推荐问题 -->
      <div
        v-if="showRecommended && recommendedQuestions.length > 0"
        class="recommended-questions after-chat"
      >
        <p class="rq-title">你可能还想问:</p>
        <div class="rq-list">
          <el-tag
            v-for="q in recommendedQuestions"
            :key="q"
            type="info"
            class="rq-tag"
            @click="fillQuestion(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <div class="action-row">
        <!-- 图片上传按钮 -->
        <div class="upload-row">
          <el-upload
            :before-upload="handleImageUpload"
            :show-file-list="false"
            accept=".png,.jpg,.jpeg,.gif,.bmp,.webp"
          >
            <el-button type="primary" plain size="small" :icon="Upload"
              >上传截图</el-button
            >
          </el-upload>
          <span class="upload-hint">支持粘贴截图</span>
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
      <!-- 已上传图片预览 -->
      <div v-if="uploadedImageText" class="uploaded-image-preview">
        <span class="image-text">{{ uploadedImageText }}</span>
        <el-button
          type="danger"
          size="small"
          text
          @click="uploadedImageText = ''"
          >移除</el-button
        >
      </div>
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入财税问题..."
        resize="none"
        @keydown.ctrl.enter="handleSend"
        @paste="handlePaste"
      />
      <div class="input-footer">
        <div class="footer-left">
          <!-- 基础版用户试用开关 -->
          <div
            v-if="billingStore.subscription?.tier === 'basic'"
            class="trial-switch"
          >
            <el-switch
              v-model="useTrialPro"
              size="small"
              :before-change="beforeTrialSwitch"
              @change="onTrialSwitchChange"
            />
            <span class="trial-label"
              >专业版尝鲜 (剩余{{ trialProCount }}次)</span
            >
          </div>
        </div>
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
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onActivated, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "@/stores/user";
import { useBillingStore } from "@/stores/billing";
import api from "@/api";
import MarkdownContent from "@/components/MarkdownContent.vue";

const userStore = useUserStore();
const billingStore = useBillingStore();

const messages = ref([]);
const inputMessage = ref("");
const isLoading = ref(false);
const useMemory = ref(true);
const messageListRef = ref(null);

// 推荐问题显示控制
const showRecommended = ref(false);

// 收藏功能（数据库存储）
const favoriteIds = ref(new Set());

const isFavorited = (msg) => {
  return favoriteIds.value.has(msg.id);
};

const toggleFavorite = async (msg) => {
  if (isFavorited(msg)) {
    // 取消收藏 - 需要找到对应的收藏ID
    try {
      const res = await api.getFavorites(1, 100);
      if (res.status === "success") {
        const fav = res.data.favorites.find(
          (f) => f.message_id === String(msg.id)
        );
        if (fav) {
          await api.deleteFavorite(fav.id);
          favoriteIds.value.delete(msg.id);
          ElMessage.success("已取消收藏");
        }
      }
    } catch (e) {
      ElMessage.error("取消收藏失败");
    }
  } else {
    // 添加收藏
    try {
      await api.addFavorite({
        content: msg.content,
        session_id: currentSessionId.value || "default",
        source: "财税专家对话",
        message_id: String(msg.id),
      });
      favoriteIds.value.add(msg.id);
      ElMessage.success("已收藏");
    } catch (e) {
      ElMessage.error("收藏失败");
    }
  }
};

const loadFavoriteIds = async () => {
  try {
    const res = await api.getFavorites(1, 100);
    if (res.status === "success") {
      res.data.favorites.forEach((f) => {
        if (f.message_id) {
          favoriteIds.value.add(parseInt(f.message_id));
        }
      });
    }
  } catch (e) {
    console.error("加载收藏失败", e);
  }
};

const soundEnabled = ref(localStorage.getItem("soundEnabled") !== "false");
const autoSaveDraft = ref(localStorage.getItem("autoSaveDraft") === "true");
const DRAFT_KEY = "chat_draft";

// 专业版试用
const trialProCount = ref(3);
const useTrialPro = ref(false);

// 专业版试用开关切换前校验
const beforeTrialSwitch = () => {
  if (billingStore.subscription?.tier === "pro") {
    ElMessage.info("您已经是专业版用户");
    return false;
  }
  if (trialProCount.value <= 0) {
    ElMessage.warning("本月试用次数已用完，升级专业版解锁更多");
    return false;
  }
  return true;
};

// 专业版试用开关切换后
const onTrialSwitchChange = (val) => {
  if (val) {
    ElMessage.info("已启用专业版尝鲜，本次回答将由专业版提供");
  } else {
    ElMessage.info("已取消专业版尝鲜");
  }
};

// 图片上传
const uploadedImageText = ref("");

// 粘贴截图处理
const handlePaste = async (event) => {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith("image/")) {
      event.preventDefault();
      const file = item.getAsFile();
      if (file) {
        await handleImageUpload(file);
      }
      return;
    }
  }
};

const handleImageUpload = async (file) => {
  const isImage = file.type.startsWith("image/");
  if (!isImage) {
    ElMessage.warning("请上传图片文件");
    return false;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const token = localStorage.getItem("token");
    const response = await fetch("/api/upload_image", {
      method: "POST",
      headers: { Authorization: token ? `Bearer ${token}` : "" },
      body: formData,
    });
    const res = await response.json();

    if (res.status === "success") {
      if (res.extracted_text) {
        uploadedImageText.value = res.extracted_text;
        ElMessage.success("图片上传成功，已提取文字");
      } else {
        ElMessage.success("图片上传成功");
      }
    } else {
      ElMessage.error(res.detail || "上传失败");
    }
  } catch (e) {
    ElMessage.error("上传失败: " + e.message);
  }
  return false; // 阻止默认上传
};

// 推荐问题（默认5个）
const recommendedQuestions = ref([
  "企业所得税最新优惠政策有哪些?",
  "增值税专用发票和普通发票的区别",
  "个人所得税专项附加扣除标准",
  "公司报销哪些发票可以抵扣?",
  "小微企业税收优惠政策汇总",
]);

const fillQuestion = (q) => {
  inputMessage.value = q;
  showRecommended.value = false;
};

// 生成推荐问题
const generateRecommendedQuestions = async (userMessage, aiResponse) => {
  console.log("generateRecommendedQuestions called", {
    userMessage,
    aiResponse,
  });
  try {
    const tier = billingStore.subscription?.tier || "basic";
    console.log("Calling API with tier:", tier);
    const res = await api.getRecommendedQuestions(
      userMessage,
      aiResponse,
      tier
    );
    console.log("API response:", res);
    if (
      res.status === "success" &&
      res.data.questions &&
      res.data.questions.length > 0
    ) {
      recommendedQuestions.value = res.data.questions;
      showRecommended.value = true;
    } else {
      console.log("未生成推荐问题:", res);
    }
  } catch (e) {
    console.error("生成推荐问题失败:", e);
  }
};

let msgId = 0;
const currentSessionId = ref("");

const copyMsg = async (content) => {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(content);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = content;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    ElMessage.success("已复制");
  } catch {
    ElMessage.error("复制失败");
  }
};

const showFeedbackDialog = ref(false);
const feedbackRating = ref("");
const feedbackReason = ref("");
const currentFeedbackMsg = ref(null);
const feedbackReasons = [
  "回答不准确",
  "回答不完整",
  "回答难以理解",
  "不符合政策规定",
  "其他",
];

const handleFeedback = async (msg, rating) => {
  if (!localStorage.getItem("token")) {
    ElMessage.warning("请先登录");
    return;
  }
  currentFeedbackMsg.value = msg;
  feedbackRating.value = rating;

  if (rating === "dislike") {
    // 差评：显示内联原因选择
    msg.showDislikeReason = !msg.showDislikeReason;
  } else {
    // 好评：直接提交
    await submitFeedback(msg, rating, "good");
    ElMessage.info("感谢您的好评");
  }
};

const submitFeedback = async (msg, rating, reason) => {
  try {
    const sessionId = currentSessionId.value || "default";
    await api.submitFeedback({
      session_id: sessionId,
      message_index: msg.id,
      rating,
      reason,
    });
    msg.showFeedback = false;
    msg.showDislikeReason = false;
  } catch (error) {
    console.error("提交评价失败", error);
    ElMessage.error("评价提交失败，请重试");
  }
};

const confirmInlineDislike = async (msg) => {
  if (!feedbackReason.value) {
    ElMessage.warning("请选择差评原因");
    return;
  }
  await submitFeedback(msg, "dislike", feedbackReason.value);
  ElMessage.info("感谢您的反馈");
};

const playSound = () => {
  if (!soundEnabled.value) return;
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 800;
    osc.type = "sine";
    gain.gain.value = 0.1;
    osc.start();
    setTimeout(() => osc.stop(), 100);
  } catch {}
};

const saveDraft = () => {
  if (autoSaveDraft.value && inputMessage.value.trim()) {
    localStorage.setItem(DRAFT_KEY, inputMessage.value);
  }
};

const loadDraft = () => {
  if (autoSaveDraft.value) {
    const draft = localStorage.getItem(DRAFT_KEY);
    if (draft) inputMessage.value = draft;
  }
};

const clearDraft = () => localStorage.removeItem(DRAFT_KEY);

watch(inputMessage, saveDraft);

const formatTime = () => {
  const now = new Date();
  return now.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

const scrollBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
    }
  });
};

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  // 发送新消息时隐藏推荐问题
  showRecommended.value = false;

  if (billingStore.tokenBalance <= 0) {
    ElMessageBox.confirm("Token余额不足，请先充值", "余额不足", {
      confirmButtonText: "去充值",
      cancelButtonText: "取消",
    })
      .then(() => {
        window.location.href = "/billing";
      })
      .catch(() => {});
    return;
  }

  // 组装消息内容（包含图片文字）
  let fullContent = inputMessage.value.trim();
  if (uploadedImageText.value) {
    fullContent = `[用户上传了截图，提取的文字内容:]\n${
      uploadedImageText.value
    }\n\n[用户问题:]\n${inputMessage.value.trim()}`;
  }

  const userMsg = {
    id: ++msgId,
    role: "user",
    content: fullContent,
    time: formatTime(),
  };

  messages.value.push(userMsg);
  const userInput = fullContent;
  inputMessage.value = "";
  uploadedImageText.value = ""; // 清空图片文字
  clearDraft();
  scrollBottom();

  // 记录是否使用试用专业版
  const isTrialPro =
    useTrialPro.value && billingStore.subscription?.tier === "basic";
  // 实际使用的版本
  const actualAgentType = isTrialPro
    ? "pro"
    : billingStore.subscription?.tier || "basic";
  // 重置试用标记（只本次有效）
  if (isTrialPro) {
    useTrialPro.value = false;
  }

  // 创建 AI 消息占位（使用 reactive 确保响应式更新）
  const aiMsg = reactive({
    id: ++msgId,
    role: "assistant",
    content: "",
    time: formatTime(),
    references: [],
    streaming: true, // 标记为流式进行中
    agentType: actualAgentType, // 记录实际使用的版本
  });
  messages.value.push(aiMsg);

  isLoading.value = true;

  try {
    await api.chatStream(
      {
        message: userInput,
        user_id: userStore.userInfo.user_id,
        use_memory: useMemory.value,
        conversation_history_limit: 10,
        trial_pro: isTrialPro,
      },
      {
        onChunk: (chunk) => {
          aiMsg.content += chunk;
          scrollBottom();
        },
        onFinish: (data) => {
          aiMsg.streaming = false;
          aiMsg.references = data.references || [];
          playSound();
          billingStore.fetchTokenBalance();
          scrollBottom();
          // 生成推荐问题
          generateRecommendedQuestions(userInput, aiMsg.content);
        },
        onError: (error) => {
          aiMsg.streaming = false;
          aiMsg.content = error || "发送失败";
          scrollBottom();
        },
      }
    );
  } catch (err) {
    aiMsg.streaming = false;
    aiMsg.content = err.message || "发送失败";
    scrollBottom();
  } finally {
    isLoading.value = false;
  }
};

const handleExport = () => {
  if (messages.value.length === 0) {
    ElMessage.warning("暂无对话");
    return;
  }
  let content = `对话导出 - ${new Date().toLocaleString("zh-CN")}\n${"=".repeat(
    50
  )}\n\n`;
  messages.value.forEach((m) => {
    content += `[${m.time}] ${m.role === "user" ? "用户" : "AI"}:\n${
      m.content
    }\n\n`;
  });
  // \u6dfb\u52a0\u514d\u8d23\u58f0\u660e
  content += `\n${"=".repeat(
    50
  )}\n\u514d\u8d23\u58f0\u660e: \u672c\u5bf9\u8bdd\u5185\u5bb9\u7531AI\u751f\u6210,\u4ec5\u4f9b\u53c2\u8003, \u4e0d\u6784\u6210\u4e13\u4e1a\u8d22\u7a0e\u5efa\u8bae\u3002\u5982\u9700\u51c6\u786e\u4fe1\u606f, \u8bf7\u54a8\u8be2\u6301\u8bc1\u8d22\u7a0e\u4e13\u5bb6\u3002`;
  const blob = new Blob(["\ufeff" + content], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `对话记录_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success("已导出");
};

const getRefSource = (ref) => {
  const source = ref.source || "";
  // 从完整路径中提取文件名
  if (source.includes("/")) {
    return source.split("/").pop();
  }
  return source || "未知来源";
};

const saveReference = async (ref, refs) => {
  if (ref.saved || ref.saving) return;
  ref.saving = true;
  try {
    const res = await api.saveReferenceDocument(
      ref.doc_id,
      ref.source,
      "tax_basic"
    );
    if (res.status === "success") {
      ref.saved = true;
      ElMessage.success(res.message || "已保存到知识库");
    }
  } catch {
    ElMessage.error("保存失败");
  } finally {
    ref.saving = false;
  }
};

const saveAllReferences = async (refs) => {
  for (const ref of refs) {
    if (!ref.saved && !ref.saving) {
      await saveReference(ref, refs);
    }
  }
};

const handleClearChat = async () => {
  await ElMessageBox.confirm("确定清空当前对话？", "提示", { type: "warning" });
  try {
    await api.clearConversationHistory(userStore.userInfo.user_id);
    messages.value = [];
    ElMessage.success("已清空");
  } catch {
    ElMessage.error("清空失败");
  }
};

const loadHistory = async () => {
  try {
    const res = await api.getConversationHistory(userStore.userInfo.user_id, {
      limit: 50,
    });
    if (res.status === "success" && res.data.length) {
      messages.value = res.data.map((m) => ({
        id: ++msgId,
        role: m.role,
        content: m.content,
        references: m.references || [],
        time: m.time || formatTime(),
        agentType: m.agent_type === "tax_pro" ? "pro" : "basic",
      }));
      scrollBottom();
    }
  } catch {}
};

onMounted(async () => {
  await billingStore.init();
  loadHistory();
  loadDraft();
  loadFavoriteIds();
  fetchTrialCount();
});

const fetchTrialCount = async () => {
  try {
    const res = await api.getTrialCount();
    if (res.status === "success" && res.data?.trial_pro_count) {
      trialProCount.value = Number(res.data.trial_pro_count);
    }
  } catch (e) {
    console.error("获取试用次数失败", e);
  }
};

onActivated(() => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
    }
  });
});
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
  position: relative;
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
  align-items: center;
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
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.message-item.user {
  /* flex-direction: row-reverse; */
}

.message-role {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.avatar {
  flex-shrink: 0;
}

.message-body {
  /* max-width: 70%; */
  min-width: 60px;
}

@media (max-width: 480px) {
  .message-item {
    position: relative;
    /* padding-left: 36px; */
    padding-right: 0;
  }

  .message-item.user {
    padding-left: 0;
    /* padding-right: 36px; */
  }

  .avatar {
    /* position: absolute; */
    /* left: 0;
    top: 0; */
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
  flex-direction: column;
  font-size: 12px;
}

.message-item.user .message-role {
  flex-direction: row-reverse;
}

.message-item.user .message-meta {
  flex-direction: column;
  align-items: flex-end;
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

.message-item.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
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
  position: relative;
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trial-switch {
  display: flex;
  align-items: center;
  gap: 6px;
}

.trial-label {
  font-size: 12px;
  color: #909399;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.uploaded-image-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 12px;
}

.uploaded-image-preview .image-text {
  flex: 1;
  color: #606266;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background: #409eff;
  animation: blink 1s infinite;
  margin-right: 4px;
  vertical-align: middle;
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}

/* 流式消息中的光标 */
.message-item.assistant .message-text:not(.loading) .typing-cursor-inline {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #409eff;
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
  content: "";
  animation: dots 1.5s infinite;
}

@keyframes dots {
  0%,
  20% {
    content: ".";
  }
  40% {
    content: "..";
  }
  60%,
  100% {
    content: "...";
  }
}

/* 内联差评原因选择 */
.dislike-reason-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  padding: 6px 10px;
  background: #fff5f5;
  border-radius: 4px;
  max-width: 320px;
}

/* 推荐问题 */
.recommended-questions {
  margin-top: 20px;
  text-align: left;
  max-width: 500px;
}

.rq-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 10px;
}

.rq-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rq-tag {
  cursor: pointer;
}

.rq-tag:hover {
  opacity: 0.8;
}

/* 对话后的推荐问题 */
.recommended-questions.after-chat {
  margin: 20px auto;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  max-width: 600px;
}

.recommended-questions.after-chat .rq-tag {
  white-space: normal;
  word-break: break-word;
  text-align: left;
  height: auto;
  min-height: 32px;
  line-height: 1.4;
  padding: 6px 12px;
}
</style>