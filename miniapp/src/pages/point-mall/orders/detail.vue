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

<style scoped>
.order-detail-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 120rpx;
}

.loading,
.error {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 200rpx 0;
  color: #999;
}

/* 状态区域 */
.status-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60rpx 30rpx 40rpx;
}

.status-header {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.status-icon {
  font-size: 60rpx;
  line-height: 1;
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.status-text {
  font-size: 40rpx;
  font-weight: bold;
  color: #fff;
}

.status-hint {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

/* 通用区块样式 */
.product-section,
.address-section,
.shipment-section,
.notes-section {
  margin-top: 20rpx;
  padding: 30rpx;
  background-color: #fff;
}

.section-title {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 20rpx;
}

/* 商品信息 */
.product-card {
  display: flex;
  gap: 20rpx;
}

.product-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.product-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  font-size: 60rpx;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8rpx 0;
}

.product-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.product-meta {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.order-number {
  font-size: 24rpx;
  color: #666;
}

.order-time {
  font-size: 24rpx;
  color: #999;
}

.product-points {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  padding: 8rpx 0;
}

.product-points .points {
  font-size: 36rpx;
  font-weight: bold;
  color: #ff4d4f;
}

.product-points .label {
  font-size: 24rpx;
  color: #999;
}

/* 地址卡片 */
.address-card {
  padding: 24rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
}

.address-top {
  display: flex;
  gap: 20rpx;
  margin-bottom: 16rpx;
}

.contact-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
}

.contact-phone {
  font-size: 28rpx;
  color: #666;
}

.address-detail {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

/* 物流卡片 */
.shipment-card {
  padding: 24rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
}

.shipment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shipment-item .label {
  font-size: 28rpx;
  color: #666;
}

.shipment-item .value {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

/* 备注卡片 */
.notes-card {
  padding: 24rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.note-item {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

.note-item.admin {
  color: #ff4d4f;
}

/* 处理时间 */
.process-time-section {
  margin-top: 20rpx;
  padding: 30rpx;
  background-color: #fff;
  text-align: center;
}

.process-time {
  font-size: 26rpx;
  color: #999;
}

/* 操作按钮 */
.action-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 30rpx;
  background-color: #fff;
  border-top: 1rpx solid #eee;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.cancel-btn {
  width: 100%;
  height: 88rpx;
  background-color: #fff;
  border: 1rpx solid #d9d9d9;
  border-radius: 44rpx;
  color: #666;
  font-size: 32rpx;
  line-height: 88rpx;
  text-align: center;
}

.cancel-btn::after {
  border: none;
}
</style>
