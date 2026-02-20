<template>
  <view class="membership-page">
    <view class="header">
      <text class="title">会员中心</text>
      <text class="subtitle">解锁更多功能</text>
    </view>

    <!-- 激活的会员 -->
    <view v-if="activeMembership && activeMembership.id" class="active-card">
      <view class="active-info">
        <text class="active-title">当前会员：{{ activeMembership.name || '未知套餐' }}</text>
        <text v-if="activeMembership.end_date" class="active-date">
          有效期至：{{ formatDate(activeMembership.end_date) }}
        </text>
        <text v-if="activeMembership.days_remaining !== undefined" class="active-days">
          剩余 {{ activeMembership.days_remaining }} 天
        </text>
      </view>
    </view>

    <!-- 会员套餐列表 -->
    <view class="packages-section">
      <view class="section-title">会员套餐</view>
      <view class="packages-list">
        <view
          v-for="pkg in packages"
          :key="pkg.id"
          class="package-card"
          :class="{ recommended: pkg.name.includes('年') }"
          @click="selectPackage(pkg)"
        >
          <view v-if="pkg.name.includes('年')" class="package-badge">
            <text>推荐</text>
          </view>
          <text class="package-name">{{ pkg.name }}</text>
          <view class="package-price">
            <text class="price-symbol">¥</text>
            <text class="price-value">{{ (pkg.price / 100).toFixed(2) }}</text>
          </view>
          <text class="package-duration">{{ pkg.duration_days }}天</text>
          <view v-if="pkg.description" class="package-desc">
            <text>{{ pkg.description }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 会员权益 -->
    <view class="benefits-section">
      <view class="section-title">会员权益</view>
      <view class="benefits-list">
        <view class="benefit-item">
          <text class="benefit-icon">✓</text>
          <text class="benefit-text">专属主题皮肤</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-icon">✓</text>
          <text class="benefit-text">数据报告</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-icon">✓</text>
          <text class="benefit-text">无广告体验</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-icon">✓</text>
          <text class="benefit-text">优先客服支持</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getMemberships,
  getActiveMembership,
  createMembershipOrder,
  type MembershipItem,
  type ActiveMembership,
} from '@/api/membership'
import { createPayment, requestWeChatPayment, verifyPayment } from '@/api/payment'

const packages = ref<MembershipItem[]>([])
const activeMembership = ref<ActiveMembership | null>(null)
const loading = ref(true)
const submitting = ref(false) // 防止重复提交

// 生成幂等性key - 使用加密安全的随机数生成
// SECURITY: 支付幂等性密钥必须使用加密安全随机数，防止密钥冲突
// 使用 crypto.getRandomValues() 而非 Math.random()
const generateIdempotencyKey = () => {
  // 使用时间戳（36进制）提供时间维度唯一性
  const timestamp = Date.now().toString(36)

  // 使用加密安全的随机数生成器
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)

  // 转换为16进制字符串
  const random = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')

  return `${timestamp}-${random}`
}

// 支付验证重试逻辑 - 指数退避
async function verifyPaymentWithRetry(
  orderId: string,
  maxRetries = 3
): Promise<{ success: boolean; message?: string }> {
  for (let i = 0; i < maxRetries; i++) {
    const verifyRes = await verifyPayment(orderId)
    if (verifyRes.success) {
      return verifyRes
    }

    // 如果不是最后一次重试，等待后重试
    if (i < maxRetries - 1) {
      // 指数退避: 1s, 2s, 4s
      const delay = Math.pow(2, i) * 1000
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  return { success: false, message: '支付确认超时，请稍后刷新查看' }
}

onMounted(async () => {
  try {
    const [pkgsRes, active] = await Promise.all([getMemberships(), getActiveMembership()])
    packages.value = pkgsRes.items.filter(pkg => pkg.is_active)
    // 检查active是否有有效的id，再赋值
    if (active && typeof active === 'object' && 'id' in active && active.id) {
      activeMembership.value = active as ActiveMembership
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const selectPackage = async (pkg: MembershipItem) => {
  // 防止重复提交
  if (submitting.value) {
    uni.showToast({ title: '请稍候，正在处理...', icon: 'none' })
    return
  }

  uni.showModal({
    title: '确认购买',
    content: `确认购买 ${pkg.name}？\n价格：¥${(pkg.price / 100).toFixed(2)}`,
    success: async res => {
      if (res.confirm) {
        submitting.value = true
        const idempotencyKey = generateIdempotencyKey()

        try {
          // 1. 创建订单（带幂等性key）
          const orderRes = await createMembershipOrder({
            membership_id: pkg.id,
            amount: pkg.price,
            payment_method: 'wechat',
            idempotency_key: idempotencyKey,
          })

          // 安全地提取订单ID
          if (!orderRes || typeof orderRes !== 'object' || !('id' in orderRes) || !orderRes.id) {
            throw new Error('订单创建失败')
          }
          const orderId = orderRes.id

          // 2. 创建支付参数
          const payRes = await createPayment({ order_id: orderId })

          if (!payRes.success || !payRes.data) {
            uni.showToast({ title: payRes.message || '支付参数生成失败', icon: 'none' })
            return
          }

          // 验证支付参数
          if (
            !payRes.data.timeStamp ||
            !payRes.data.nonceStr ||
            !payRes.data.package ||
            !payRes.data.paySign
          ) {
            uni.showToast({ title: '支付参数异常', icon: 'none' })
            return
          }

          // 3. 调起微信支付
          try {
            await requestWeChatPayment(payRes.data)

            // 4. 验证支付结果（带重试逻辑）
            uni.showLoading({ title: '确认支付结果...', mask: true })

            const verifyRes = await verifyPaymentWithRetry(orderId)

            uni.hideLoading()

            if (!verifyRes.success) {
              uni.showToast({ title: verifyRes.message || '支付验证失败', icon: 'none' })
              return
            }

            // 5. 支付成功，刷新会员状态
            uni.showToast({ title: '支付成功', icon: 'success' })
            setTimeout(async () => {
              try {
                const active = await getActiveMembership()
                if (active && typeof active === 'object' && 'id' in active && active.id) {
                  activeMembership.value = active as ActiveMembership
                }
              } catch (e) {
                console.error('Failed to refresh membership:', e)
              }
            }, 1000)
          } catch (paymentError: any) {
            if (paymentError.errMsg && paymentError.errMsg.includes('cancel')) {
              uni.showToast({ title: '已取消支付', icon: 'none' })
            } else {
              uni.showToast({ title: '支付失败，请重试', icon: 'none' })
            }
          }
        } catch (error: any) {
          const errorMsg = error?.message || '创建订单失败，请重试'
          uni.showToast({ title: errorMsg, icon: 'none' })
        } finally {
          submitting.value = false
        }
      }
    },
  })
}
</script>

<style scoped>
.membership-page {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  margin-bottom: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
}

.subtitle {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-top: 10rpx;
}

.active-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.active-info {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.active-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #fff;
}

.active-date {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
}

.active-days {
  font-size: 28rpx;
  color: #ffd700;
  font-weight: bold;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.packages-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.package-card {
  position: relative;
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  text-align: center;
  border: 4rpx solid transparent;
}

.package-card.recommended {
  border-color: #5470c6;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.package-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #ff6b6b;
  color: #fff;
  font-size: 20rpx;
  padding: 8rpx 16rpx;
  border-bottom-left-radius: 16rpx;
}

.package-name {
  font-size: 36rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 16rpx;
}

.package-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 12rpx;
}

.price-symbol {
  font-size: 28rpx;
  color: #ff6b6b;
  margin-right: 4rpx;
}

.price-value {
  font-size: 56rpx;
  font-weight: bold;
  color: #ff6b6b;
}

.package-duration {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 16rpx;
}

.package-desc {
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
}

.benefits-section {
  margin-top: 30rpx;
}

.benefits-list {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.benefit-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.benefit-item:last-child {
  border-bottom: none;
}

.benefit-icon {
  width: 48rpx;
  height: 48rpx;
  background: #91cc75;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: bold;
  margin-right: 20rpx;
}

.benefit-text {
  font-size: 28rpx;
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
