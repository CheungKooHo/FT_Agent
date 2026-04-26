<template>
  <div class="billing-container">
    <div class="balance-section">
      <div class="balance-card">
        <div class="balance-icon">
          <el-icon :size="32"><Coin /></el-icon>
        </div>
        <div class="balance-info">
          <span class="balance-label">Token 余额</span>
          <span class="balance-value">{{ billingStore.tokenBalance }}</span>
        </div>
        <el-button type="primary" @click="openRechargeDialog">充值</el-button>
      </div>

      <div class="tier-card">
        <div class="tier-icon" :class="billingStore.subscription?.tier">
          <el-icon :size="24"><Medal /></el-icon>
        </div>
        <div class="tier-info">
          <el-tag :type="billingStore.subscription?.tier === 'pro' ? 'warning' : 'info'" effect="dark">
            {{ billingStore.subscription?.tier_name || '基础版' }}
          </el-tag>
          <span class="tier-desc">
            {{ billingStore.subscription?.tier === 'pro' ? '专业版用户' : '基础版用户' }}
          </span>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h3>订阅方案</h3>
        <span class="hint">升级后自动享受更多权益</span>
      </div>
      <div class="tier-grid">
        <div
          v-for="tier in billingStore.availableTiers"
          :key="tier.tier_code"
          class="tier-item"
          :class="{ active: billingStore.subscription?.tier === tier.tier_code }"
        >
          <div class="tier-top">
            <span class="tier-name">{{ tier.tier_name }}</span>
            <el-tag v-if="tier.tier_code === 'basic'" type="info" size="small">免费</el-tag>
            <el-tag v-else type="danger" size="small">推荐</el-tag>
          </div>
          <div class="tier-price">
            <span class="price">¥{{ (tier.price_monthly / 100).toFixed(0) }}</span>
            <span class="unit">/月</span>
          </div>
          <ul class="tier-features">
            <li>
              <el-icon><Check /></el-icon>
              {{ tier.monthly_token_quota }} Token/月
            </li>
            <li v-for="feat in tier.features" :key="feat">
              <el-icon><Check /></el-icon>
              {{ getFeatureName(feat) }}
            </li>
          </ul>
          <el-button
            :type="billingStore.subscription?.tier === tier.tier_code ? 'info' : 'primary'"
            :disabled="billingStore.subscription?.tier === tier.tier_code"
            @click="openUpgradeDialog(tier)"
          >
            {{ billingStore.subscription?.tier === tier.tier_code ? '当前版本' : '立即升级' }}
          </el-button>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h3>交易记录</h3>
        <span class="hint">{{ billingStore.transactions.length }} 笔</span>
      </div>
      <el-table :data="billingStore.transactions" stripe size="small">
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getTransactionTypeColor(row.type)" size="small">
              {{ getTransactionTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="90">
          <template #default="{ row }">
            <span :style="{ color: row.amount > 0 ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
              {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column prop="created_at" label="时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 支付弹窗 -->
    <el-dialog v-model="showPaymentDialog" title="扫码支付" width="90%" max-width="400px" :close-on-click-modal="false">
      <div v-if="paymentStep === 'form'" class="payment-form">
        <div class="payment-info">
          <p class="payment-title">{{ paymentType === 'recharge' ? 'Token 充值' : '订阅升级' }}</p>
          <p class="payment-amount">
            <span v-if="paymentType === 'recharge'">¥{{ rechargeMoney }}</span>
            <span v-else>{{ upgradeTier?.tier_name }}</span>
          </p>
          <p v-if="paymentType === 'recharge'" class="payment-price">
            约 {{ rechargeTokenAmount.toLocaleString() }} Token
          </p>
        </div>

        <!-- 充值选项（按金额） -->
        <div v-if="paymentType === 'recharge'" class="recharge-options">
          <div class="options-label">选择充值金额</div>
          <div class="options-buttons">
            <el-button
              v-for="opt in rechargeOptions"
              :key="opt.value"
              :type="rechargeMoney === opt.value ? 'primary' : 'default'"
              @click="rechargeMoney = opt.value"
            >
              ¥{{ opt.label }}
            </el-button>
          </div>
          <div class="custom-input">
            <span class="custom-label">自定义金额：</span>
            <el-input-number
              v-model="rechargeMoney"
              :min="1"
              :step="10"
              controls-position="right"
              style="width: 150px"
            />
            <span class="custom-unit">元</span>
          </div>
        </div>

        <el-form label-width="80px">
          <el-form-item label="支付方式">
            <el-radio-group v-model="paymentMethod">
              <el-radio label="alipay">支付宝</el-radio>
              <el-radio label="wechat">微信</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <div v-else-if="paymentStep === 'processing'" class="payment-status">
        <el-icon class="is-loading" :size="50"><Loading /></el-icon>
        <p>正在创建订单...</p>
      </div>

      <div v-else-if="paymentStep === 'qrcode'" class="payment-qrcode">
        <p class="qrcode-hint">请使用{{ paymentMethod === 'alipay' ? '支付宝' : '微信' }}扫码支付</p>
        <div class="qrcode-box">
          <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="支付二维码" class="qrcode-image" />
          <div v-else class="qrcode-placeholder">
            <el-icon :size="60"><Picture /></el-icon>
            <p>二维码加载中...</p>
          </div>
        </div>
        <p class="qrcode-tip">支付完成后请稍候，系统将自动更新</p>
      </div>

      <div v-else-if="paymentStep === 'success'" class="payment-status">
        <el-icon :size="60" color="#67c23a"><CircleCheck /></el-icon>
        <p class="status-text success">{{ paymentType === 'recharge' ? '充值成功' : '升级成功' }}！</p>
        <p class="status-hint">{{ paymentType === 'recharge' ? `已获得 ${rechargeTokenAmount.toLocaleString()} Token` : `已升级到 ${upgradeTier?.tier_name}` }}</p>
      </div>

      <div v-else-if="paymentStep === 'failed'" class="payment-status">
        <el-icon :size="60" color="#f56c6c"><CircleClose /></el-icon>
        <p class="status-text failed">支付失败</p>
        <p class="status-hint">订单已过期或支付失败，请重试</p>
      </div>

      <template #footer>
        <div v-if="paymentStep === 'form'">
          <el-button @click="showPaymentDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmPayment">确认支付</el-button>
        </div>
        <div v-else-if="paymentStep === 'qrcode'">
          <el-button @click="handleCancelPayment">取消支付</el-button>
        </div>
        <div v-else-if="paymentStep === 'success'">
          <el-button type="primary" @click="showPaymentDialog = false">完成</el-button>
        </div>
        <div v-else-if="paymentStep === 'failed'">
          <el-button @click="showPaymentDialog = false">关闭</el-button>
          <el-button type="primary" @click="paymentStep = 'form'; qrCodeUrl = ''">重新支付</el-button>
        </div>
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

const showPaymentDialog = ref(false)
const paymentStep = ref('form')
const paymentType = ref('recharge')
const paymentMethod = ref('alipay')
const rechargeMoney = ref(10)
const upgradeTier = ref(null)
const qrCodeUrl = ref('')

// 预设充值选项（金额：元）
const rechargeOptions = [
  { label: '10', value: 10 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
  { label: '200', value: 200 },
  { label: '500', value: 500 }
]

// 根据金额计算 Token 数量
const rechargeTokenAmount = computed(() => {
  const pricePerMillion = billingStore.tokenPrice?.price_yuan || 5
  return Math.round((rechargeMoney.value / pricePerMillion) * 1000000)
})

const openRechargeDialog = () => {
  paymentType.value = 'recharge'
  paymentStep.value = 'form'
  rechargeMoney.value = 10
  showPaymentDialog.value = true
}

const openUpgradeDialog = (tier) => {
  paymentType.value = 'upgrade'
  paymentStep.value = 'form'
  upgradeTier.value = tier
  showPaymentDialog.value = true
}

const confirmPayment = async () => {
  paymentStep.value = 'processing'

  try {
    // 1. 创建支付订单
    const orderData = {
      order_type: paymentType.value,
      amount: paymentType.value === 'recharge' ? rechargeMoney.value * 100 : upgradeTier.value.price_monthly,
      token_amount: rechargeTokenAmount.value,
      channel: paymentMethod.value
    }

    const order = await billingStore.createPaymentOrder(orderData)

    if (order.status !== 'success') {
      paymentStep.value = 'failed'
      return
    }

    // 2. 获取二维码
    qrCodeUrl.value = order.qr_code || order.code_url
    paymentStep.value = 'qrcode'

    // 3. 轮询订单状态（最多30秒）
    pollOrderStatus(order.order_id)
  } catch (error) {
    console.error('支付错误:', error)
    paymentStep.value = 'failed'
  }
}

let pollTimer = null

const pollOrderStatus = async (orderId) => {
  const maxAttempts = 15
  let attempts = 0

  const checkStatus = async () => {
    if (attempts >= maxAttempts) {
      paymentStep.value = 'failed'
      return
    }

    attempts++

    try {
      const result = await billingStore.queryPaymentStatus(orderId)

      if (result.status === 'paid') {
        paymentStep.value = 'success'
        // 刷新余额
        await billingStore.fetchTokenBalance()
        if (paymentType.value === 'upgrade') {
          await billingStore.fetchSubscription()
        }
        await billingStore.fetchTransactions()
      } else if (result.status === 'failed') {
        paymentStep.value = 'failed'
      } else {
        // 继续轮询（每2秒）
        pollTimer = setTimeout(checkStatus, 2000)
      }
    } catch (error) {
      console.error('查询状态错误:', error)
      pollTimer = setTimeout(checkStatus, 2000)
    }
  }

  checkStatus()
}

const handleCancelPayment = async () => {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
  if (qrCodeUrl.value) {
    // 尝试关闭后端订单
    try {
      await api.closePaymentOrder(qrCodeUrl.value.split('/').pop())
    } catch (e) {
      console.error('关闭订单失败:', e)
    }
  }
  qrCodeUrl.value = ''
  paymentStep.value = 'form'
}

const simulatePayment = async () => {
  paymentStep.value = 'processing'
  await new Promise(resolve => setTimeout(resolve, 2000))
  const isSuccess = Math.random() > 0.2

  if (isSuccess) {
    paymentStep.value = 'success'
    if (paymentType.value === 'recharge') {
      console.log('充值Token数量:', rechargeTokenAmount.value, '金额:', rechargeMoney.value)
      await billingStore.rechargeToken(rechargeTokenAmount.value)
    } else {
      await billingStore.upgradeSubscription(upgradeTier.value.tier_code)
    }
    await billingStore.fetchTokenBalance()
    await billingStore.fetchSubscription()
    await billingStore.fetchTransactions()
  } else {
    paymentStep.value = 'failed'
  }
}

const getFeatureName = (feat) => {
  const map = { policy_qa: '财税政策问答', analysis: '方案分析', calculation: '税费计算', advice: '专业建议' }
  return map[feat] || feat
}

const getTransactionTypeName = (type) => {
  const map = { grant: '赠送', purchase: '充值', consume: '消耗', refund: '退款' }
  return map[type] || type
}

const getTransactionTypeColor = (type) => {
  const map = { grant: 'success', purchase: 'primary', consume: 'warning', refund: 'info' }
  return map[type] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(async () => {
  await billingStore.init()
  await billingStore.fetchTransactions()
})
</script>

<style scoped>
.billing-container {
  height: 100%;
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.balance-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.balance-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.balance-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #409EFF, #67C23A);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.balance-info {
  flex: 1;
}

.balance-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.balance-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.tier-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tier-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #E6A23C, #F56C6C);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.tier-icon.basic {
  background: linear-gradient(135deg, #909399, #606266);
}

.tier-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tier-desc {
  font-size: 12px;
  color: #909399;
}

.section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.hint {
  font-size: 12px;
  color: #909399;
}

.tier-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.tier-item {
  border: 2px solid #ebeef5;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s;
}

.tier-item:hover {
  border-color: #409EFF;
}

.tier-item.active {
  border-color: #409EFF;
  background: #f0f7ff;
}

.tier-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tier-name {
  font-weight: 600;
  color: #303133;
}

.tier-price {
  margin-bottom: 12px;
}

.price {
  font-size: 28px;
  font-weight: bold;
  color: #F56C6C;
}

.unit {
  font-size: 12px;
  color: #909399;
}

.tier-features {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
}

.tier-features li {
  font-size: 13px;
  color: #606266;
  padding: 4px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tier-features li .el-icon {
  color: #67C23A;
}

.payment-form {
  text-align: center;
}

.payment-info {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.payment-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #909399;
}

.payment-amount {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #F56C6C;
}

.payment-price {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #909399;
}

.qr-box {
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
}

.qr-box p {
  margin: 8px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.qr-hint {
  font-size: 12px;
}

.payment-qrcode {
  text-align: center;
}

.qrcode-hint {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
}

.qrcode-box {
  padding: 16px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  background: #f5f7fa;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qrcode-image {
  max-width: 200px;
  max-height: 200px;
}

.qrcode-placeholder {
  color: #909399;
  text-align: center;
}

.qrcode-placeholder p {
  margin: 8px 0 0 0;
  font-size: 14px;
}

.qrcode-tip {
  margin: 16px 0 0 0;
  font-size: 12px;
  color: #909399;
}

.payment-status {
  text-align: center;
  padding: 24px 0;
}

.payment-status p {
  margin: 12px 0 0 0;
}

.status-text {
  font-size: 18px;
  font-weight: bold;
}

.status-text.success {
  color: #67C23A;
}

.status-text.failed {
  color: #F56C6C;
}

.status-hint {
  color: #909399;
  font-size: 14px;
}

@media (max-width: 480px) {
  .billing-container {
    padding: 12px;
  }

  .balance-section {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .balance-card,
  .tier-card {
    padding: 14px;
  }

  .tier-grid {
    grid-template-columns: 1fr;
  }

  .section {
    padding: 14px;
  }
}

@media (min-width: 768px) {
  .billing-container {
    padding: 24px;
  }

  .balance-section {
    gap: 16px;
  }

  .balance-card,
  .tier-card {
    padding: 20px;
  }

  .balance-value {
    font-size: 32px;
  }

  .section {
    padding: 20px;
  }
}

.recharge-options {
  margin-bottom: 16px;
}

.options-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}

.options-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.options-buttons .el-button {
  flex: 1;
  min-width: 80px;
}

.custom-input {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.custom-label {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.custom-unit {
  font-size: 13px;
  color: #909399;
}
</style>
