<template>
  <view class="orders-page">
    <view class="header">
      <text class="title">我的订单</text>
    </view>

    <view v-if="orders.length > 0" class="orders-list">
      <view v-for="order in orders" :key="order.id" class="order-card">
        <view class="order-header">
          <text class="order-id">订单号：{{ order.id.slice(0, 8) }}...</text>
          <view class="order-status" :class="getStatusClass(order.status)">
            <text>{{ getStatusText(order.status) }}</text>
          </view>
        </view>

        <view class="order-info">
          <view class="info-row">
            <text class="info-label">套餐ID</text>
            <text class="info-value">{{ order.membership_id }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">金额</text>
            <text class="info-value price">¥{{ (order.amount / 100).toFixed(2) }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">开始日期</text>
            <text class="info-value">{{ formatDate(order.start_date) }}</text>
          </view>
          <view v-if="order.end_date" class="info-row">
            <text class="info-label">结束日期</text>
            <text class="info-value">{{ formatDate(order.end_date) }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">下单时间</text>
            <text class="info-value">{{ formatDateTime(order.created_at) }}</text>
          </view>
          <view v-if="order.auto_renew" class="info-row">
            <text class="info-label">自动续费</text>
            <text class="info-value">已开启</text>
          </view>
        </view>

        <view v-if="order.status === 'pending'" class="order-actions">
          <button class="action-btn primary" @click="handlePay(order)">
            <text>去支付</text>
          </button>
          <button class="action-btn secondary" @click="handleCancel(order)">
            <text>取消订单</text>
          </button>
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">
      <text class="empty-icon">📋</text>
      <text class="empty-text">暂无订单</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyOrders, cancelOrder } from '@/api/membership'
import { createPayment, requestWeChatPayment } from '@/api/payment'

const orders = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getMyOrders()
    orders.value = res.items
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    refunded: '已退款',
  }
  return statusMap[status] || status
}

const getStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    pending: 'status-pending',
    paid: 'status-paid',
    cancelled: 'status-cancelled',
    refunded: 'status-refunded',
  }
  return classMap[status] || ''
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const handlePay = async (order) => {
  try {
    // 1. 创建支付参数
    const payRes = await createPayment({ order_id: order.id })

    if (!payRes.success || !payRes.data) {
      uni.showToast({ title: payRes.message || '支付参数生成失败', icon: 'none' })
      return
    }

    // 2. 调起微信支付
    await requestWeChatPayment(payRes.data)
    uni.showToast({ title: '支付成功', icon: 'success' })

    // 3. 刷新订单列表
    setTimeout(async () => {
      const res = await getMyOrders()
      orders.value = res.items
    }, 1000)
  } catch (error: any) {
    if (error.errMsg && error.errMsg.includes('cancel')) {
      uni.showToast({ title: '已取消支付', icon: 'none' })
    } else {
      uni.showToast({ title: '支付失败，请重试', icon: 'none' })
    }
  }
}

const handleCancel = async (order) => {
  uni.showModal({
    title: '取消订单',
    content: '确认取消该订单？',
    success: async res => {
      if (res.confirm) {
        try {
          await cancelOrder(order.id)
          uni.showToast({ title: '订单已取消', icon: 'success' })

          // 刷新订单列表
          setTimeout(async () => {
            const ordersRes = await getMyOrders()
            orders.value = ordersRes.items
          }, 500)
        } catch (error: any) {
          uni.showToast({
            title: error?.message || '取消失败',
            icon: 'none',
          })
        }
      }
    },
  })
}
</script>

<style scoped>
.orders-page {
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

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.order-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.order-id {
  font-size: 26rpx;
  color: #666;
}

.order-status {
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
}

.status-pending {
  background: #fff3e0;
  color: #ff9800;
}

.status-paid {
  background: #e8f5e9;
  color: #4caf50;
}

.status-cancelled,
.status-refunded {
  background: #ffebee;
  color: #f44336;
}

.order-info {
  margin-bottom: 20rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 28rpx;
  color: #666;
}

.info-value {
  font-size: 28rpx;
  color: #333;
}

.info-value.price {
  color: #ff6b6b;
  font-weight: bold;
  font-size: 32rpx;
}

.order-actions {
  display: flex;
  gap: 20rpx;
}

.action-btn {
  flex: 1;
  height: 72rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  border: none;
}

.action-btn.primary {
  background: #5470c6;
  color: #fff;
}

.action-btn.secondary {
  background: #f5f5f5;
  color: #666;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
