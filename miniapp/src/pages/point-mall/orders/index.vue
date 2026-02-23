<template>
  <view class="orders-page">
    <!-- 状态筛选 -->
    <view class="status-filter">
      <scroll-view scroll-x class="status-scroll">
        <view
          class="status-item"
          :class="{ active: selectedStatus === '' }"
          @tap="selectStatus('')"
        >
          <text>全部</text>
        </view>
        <view
          class="status-item"
          :class="{ active: selectedStatus === 'pending' }"
          @tap="selectStatus('pending')"
        >
          <text>待处理</text>
        </view>
        <view
          class="status-item"
          :class="{ active: selectedStatus === 'completed' }"
          @tap="selectStatus('completed')"
        >
          <text>已完成</text>
        </view>
        <view
          class="status-item"
          :class="{ active: selectedStatus === 'cancelled' }"
          @tap="selectStatus('cancelled')"
        >
          <text>已取消</text>
        </view>
      </scroll-view>
    </view>

    <!-- 订单列表 -->
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="orders.length === 0" class="empty">
      <text>暂无订单</text>
    </view>

    <view v-else class="orders-list">
      <view v-for="order in orders" :key="order.id" class="order-item">
        <view class="order-header">
          <text class="order-number">订单号：{{ order.order_number }}</text>
          <view class="order-status" :class="'status-' + order.status">
            <text>{{ getStatusText(order.status) }}</text>
          </view>
        </view>

        <view class="order-content">
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
            <text class="order-time">{{ formatTime(order.created_at) }}</text>
          </view>

          <view class="order-points">
            <text class="points">-{{ order.points_cost }}</text>
            <text class="label">积分</text>
          </view>
        </view>

        <view v-if="order.status === 'pending'" class="order-actions">
          <button class="cancel-btn" @tap="handleCancel(order)">取消订单</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyPointOrders, cancelPointOrder } from '@/api/pointShop'

const orders = ref([])
const loading = ref(false)
const selectedStatus = ref('')

onMounted(() => {
  loadOrders()
})

async function loadOrders() {
  try {
    loading.value = true
    const res = await getMyPointOrders(selectedStatus.value || undefined)
    orders.value = res.orders || []
  } catch (err) {
    console.error('Failed to load orders:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function selectStatus(status) {
  selectedStatus.value = status
  loadOrders()
}

async function handleCancel(order) {
  try {
    const result = await uni.showModal({
      title: '确认取消',
      content: '确定要取消这个订单吗？积分将原路退回。',
    })

    if (!result.confirm) return

    uni.showLoading({ title: '处理中...' })

    await cancelPointOrder(order.id)

    uni.hideLoading()

    uni.showToast({
      title: '订单已取消',
      icon: 'success',
    })

    // 重新加载列表
    loadOrders()
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

function formatTime(timeStr) {
  const date = new Date(timeStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}月${day}日 ${hour}:${minute}`
}
</script>

<style lang="scss" scoped>
.orders-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 20rpx;
}

.status-filter {
  background: white;
  padding: 20rpx 0;
  margin-bottom: 20rpx;

  .status-scroll {
    white-space: nowrap;
    padding: 0 20rpx;

    .status-item {
      display: inline-block;
      padding: 10rpx 25rpx;
      margin-right: 15rpx;
      border-radius: 30rpx;
      font-size: 26rpx;
      background: #f5f5f5;
      color: #666;

      &.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
    }
  }
}

.loading,
.empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.orders-list {
  padding: 20rpx;

  .order-item {
    background: white;
    border-radius: 20rpx;
    overflow: hidden;
    margin-bottom: 20rpx;

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20rpx;
      border-bottom: 1rpx solid #f0f0f0;

      .order-number {
        font-size: 24rpx;
        color: #999;
      }

      .order-status {
        font-size: 24rpx;
        padding: 5rpx 15rpx;
        border-radius: 15rpx;

        &.status-pending {
          background: #fff7e6;
          color: #fa8c16;
        }

        &.status-completed {
          background: #f6ffed;
          color: #52c41a;
        }

        &.status-cancelled,
        &.status-refunded {
          background: #f5f5f5;
          color: #999;
        }
      }
    }

    .order-content {
      display: flex;
      padding: 20rpx;

      .product-image {
        width: 140rpx;
        height: 140rpx;
        border-radius: 15rpx;
        flex-shrink: 0;

        &.placeholder {
          background: #f0f0f0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 50rpx;
        }
      }

      .product-info {
        flex: 1;
        padding: 0 20rpx;
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        .product-name {
          font-size: 28rpx;
          font-weight: bold;
        }

        .order-time {
          font-size: 24rpx;
          color: #999;
        }
      }

      .order-points {
        text-align: right;

        .points {
          display: block;
          font-size: 32rpx;
          font-weight: bold;
          color: #ff4d4f;
        }

        .label {
          font-size: 22rpx;
          color: #999;
        }
      }
    }

    .order-actions {
      padding: 15rpx 20rpx;
      border-top: 1rpx solid #f0f0f0;

      .cancel-btn {
        width: 100%;
        background: white;
        color: #999;
        border: 1rpx solid #d9d9d9;
        border-radius: 10rpx;
        padding: 15rpx;
        font-size: 26rpx;

        &::after {
          border: none;
        }
      }
    }
  }
}
</style>
