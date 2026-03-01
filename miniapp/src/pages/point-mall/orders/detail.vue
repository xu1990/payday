<template>
  <view class="order-detail-page">
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="!order" class="error">
      <text>订单不存在</text>
    </view>

    <view v-else class="detail-content">
      <!-- 订单状态 -->
      <view class="status-section">
        <view class="status-header" :class="'status-' + order.status">
          <text class="status-icon">{{ getStatusIcon(order.status) }}</text>
          <view class="status-info">
            <text class="status-text">{{ getStatusText(order.status) }}</text>
            <text v-if="order.status === 'pending'" class="status-hint">
              工作人员会尽快处理您的订单
            </text>
            <text v-else-if="order.status === 'completed'" class="status-hint">
              订单已完成，感谢您的兑换
            </text>
            <text v-else-if="order.status === 'cancelled'" class="status-hint">
              订单已取消，积分已退回
            </text>
            <text v-else-if="order.status === 'refunded'" class="status-hint">
              订单已退款，积分已退回
            </text>
          </view>
        </view>
      </view>

      <!-- 商品信息 -->
      <view class="product-section">
        <view class="section-title">商品信息</view>
        <view class="product-card">
          <image
            v-if="order.product_image"
            class="product-image"
            :src="order.product_image"
            mode="aspectFill"
          />
          <view v-else class="product-image placeholder">
            <text>🎁</text>
          </view>
          <view class="product-info">
            <text class="product-name">{{ order.product_name }}</text>
            <view class="product-meta">
              <text class="order-number">订单号：{{ order.order_number }}</text>
              <text class="order-time">{{ formatFullTime(order.created_at) }}</text>
            </view>
          </view>
          <view class="product-points">
            <text class="points">-{{ order.points_cost }}</text>
            <text class="label">积分</text>
          </view>
        </view>
      </view>

      <!-- 支付信息（如果有现金支付） -->
      <view v-if="order.payment_mode !== 'points_only' || (order.cash_amount && order.cash_amount > 0)" class="payment-section">
        <view class="section-title">支付信息</view>
        <view class="payment-card">
          <view class="payment-item">
            <text class="label">支付方式</text>
            <text class="value">
              <text v-if="order.payment_mode === 'points_only'">纯积分</text>
              <text v-else-if="order.payment_mode === 'cash_only'">纯现金</text>
              <text v-else-if="order.payment_mode === 'mixed'">积分+现金</text>
            </text>
          </view>
          <view v-if="order.points_cost > 0" class="payment-item">
            <text class="label">积分</text>
            <text class="value points-value">{{ order.points_cost }} 积分</text>
          </view>
          <view v-if="order.cash_amount && order.cash_amount > 0" class="payment-item">
            <text class="label">现金</text>
            <text class="value cash-value">¥{{ (order.cash_amount / 100).toFixed(2) }}</text>
          </view>
        </view>
      </view>

      <!-- 收货地址（如果有） -->
      <view v-if="order.address" class="address-section">
        <view class="section-title">收货地址</view>
        <view class="address-card">
          <view class="address-top">
            <text class="contact-name">{{ order.address.contact_name }}</text>
            <text class="contact-phone">{{ order.address.contact_phone }}</text>
          </view>
          <view class="address-detail">
            <text>{{ order.address.province_name }}{{ order.address.city_name }}{{ order.address.district_name }}</text>
            <text>{{ order.address.detailed_address }}</text>
          </view>
        </view>
      </view>

      <!-- 物流信息（如果有） -->
      <view v-if="order.shipment_id" class="shipment-section">
        <view class="section-title">物流信息</view>
        <view class="shipment-card">
          <view class="shipment-item">
            <text class="label">物流单号：</text>
            <text class="value">{{ order.shipment_id }}</text>
          </view>
          <!-- 这里可以扩展更多物流信息 -->
        </view>
      </view>

      <!-- 订单备注（如果有） -->
      <view v-if="order.notes || order.delivery_info" class="notes-section">
        <view class="section-title">订单备注</view>
        <view class="notes-card">
          <text v-if="order.delivery_info" class="note-item">
            交付信息：{{ order.delivery_info }}
          </text>
          <text v-if="order.notes" class="note-item">
            用户备注：{{ order.notes }}
          </text>
          <text v-if="order.notes_admin" class="note-item admin">
            管理员备注：{{ order.notes_admin }}
          </text>
        </view>
      </view>

      <!-- 处理时间（如果有） -->
      <view v-if="order.processed_at" class="process-time-section">
        <text class="process-time">处理时间：{{ formatFullTime(order.processed_at) }}</text>
      </view>

      <!-- 操作按钮 -->
      <view v-if="order.status === 'pending'" class="action-section">
        <button class="cancel-btn" @tap="handleCancel">取消订单</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPointOrderDetail, cancelPointOrder } from '@/api/pointShop'

const order = ref(null)
const loading = ref(false)
const orderId = ref('')

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || {}
  orderId.value = options.id || ''

  if (orderId.value) {
    loadOrderDetail()
  }
})

async function loadOrderDetail() {
  try {
    loading.value = true
    order.value = await getPointOrderDetail(orderId.value)
  } catch (err) {
    console.error('Failed to load order detail:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

async function handleCancel() {
  if (!order.value) return

  try {
    const result = await uni.showModal({
      title: '确认取消',
      content: '确定要取消这个订单吗？积分将原路退回。',
    })

    if (!result.confirm) return

    uni.showLoading({ title: '处理中...' })

    await cancelPointOrder(orderId.value)

    uni.hideLoading()

    uni.showToast({
      title: '订单已取消',
      icon: 'success',
    })

    // 重新加载详情
    await loadOrderDetail()
  } catch (err) {
    uni.hideLoading()
    console.error('Cancel failed:', err)
    uni.showToast({
      title: err.message || '取消失败',
      icon: 'none',
    })
  }
}

function getStatusText(status) {
  const statusMap = {
    pending: '待处理',
    completed: '已完成',
    cancelled: '已取消',
    refunded: '已退款',
  }
  return statusMap[status] || status
}

function getStatusIcon(status) {
  const iconMap = {
    pending: '⏳',
    completed: '✅',
    cancelled: '❌',
    refunded: '💰',
  }
  return iconMap[status] || '📦'
}

function formatFullTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}
</script>

<style lang="scss" scoped>
.order-detail-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 120rpx;
}

.loading,
.error {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: $spacing-2xl 0;
  color: var(--text-tertiary);
}

/* 状态区域 */
.status-section {
  background: $gradient-brand;
  padding: $spacing-xl $spacing-lg $spacing-lg;
}

.status-header {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;
}

.status-icon {
  font-size: 60rpx;
  line-height: 1;
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.status-text {
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: #fff;
}

.status-hint {
  font-size: $font-size-sm;
  color: rgba(255, 255, 255, 0.9);
}

/* 通用区块样式 */
.product-section,
.payment-section,
.address-section,
.shipment-section,
.notes-section {
  margin-top: $spacing-md;
  padding: $spacing-lg;
  @include glass-card();
}

/* 支付信息 */
.payment-card {
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.payment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-sm 0;

  &:not(:last-child) {
    border-bottom: 1rpx solid var(--border-subtle);
  }
}

.payment-item .label {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.payment-item .value {
  font-size: $font-size-sm;
  color: var(--text-primary);
  font-weight: $font-weight-medium;
}

.payment-item .points-value {
  color: $brand-primary;
}

.payment-item .cash-value {
  color: $semantic-error;
}

.section-title {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
  margin-bottom: $spacing-md;
}

/* 商品信息 */
.product-card {
  display: flex;
  gap: $spacing-md;
}

.product-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: $radius-md;
  flex-shrink: 0;
}

.product-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
  font-size: 60rpx;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: $spacing-xs 0;
}

.product-name {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
  line-height: 1.4;
}

.product-meta {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
}

.order-number {
  font-size: $font-size-xs;
  color: var(--text-secondary);
}

.order-time {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.product-points {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  padding: $spacing-xs 0;
}

.product-points .points {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $semantic-error;
}

.product-points .label {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

/* 地址卡片 */
.address-card {
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.address-top {
  display: flex;
  gap: $spacing-md;
  margin-bottom: $spacing-sm;
}

.contact-name {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
}

.contact-phone {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.address-detail {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
  font-size: $font-size-sm;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 物流卡片 */
.shipment-card {
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.shipment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shipment-item .label {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.shipment-item .value {
  font-size: $font-size-sm;
  color: var(--text-primary);
  font-weight: $font-weight-medium;
}

/* 备注卡片 */
.notes-card {
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.note-item {
  font-size: $font-size-sm;
  color: var(--text-secondary);
  line-height: 1.6;
}

.note-item.admin {
  color: $semantic-error;
}

/* 处理时间 */
.process-time-section {
  margin-top: $spacing-md;
  padding: $spacing-lg;
  @include glass-card();
  text-align: center;
}

.process-time {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

/* 操作按钮 */
.action-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: $spacing-md $spacing-lg;
  background: var(--bg-glass-standard);
  border-top: 1rpx solid var(--border-subtle);
  box-shadow: $shadow-sm;
}

.cancel-btn {
  width: 100%;
  height: 88rpx;
  background: var(--bg-glass-standard);
  border: 1rpx solid var(--border-regular);
  border-radius: $radius-full;
  color: var(--text-secondary);
  font-size: $font-size-base;
  line-height: 88rpx;
  text-align: center;
}

.cancel-btn::after {
  border: none;
}
</style>
