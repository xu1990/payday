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
      <view
        v-for="order in orders"
        :key="order.id"
        class="order-item"
        @tap="goToDetail(order)"
      >
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
            <!-- 显示现金金额（如果有） -->
            <text v-if="order.cash_amount && order.cash_amount > 0" class="cash-amount">
              +¥{{ (order.cash_amount / 100).toFixed(2) }}
            </text>
          </view>
        </view>

        <view v-if="order.status === 'pending'" class="order-actions">
          <button class="cancel-btn" @tap.stop="handleCancel(order)">取消订单</button>
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

function goToDetail(order) {
  uni.navigateTo({
    url: `/pages/point-mall/orders/detail?id=${order.id}`,
  })
}
</script>

<style lang="scss" scoped>
.orders-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #ffffff 100%);
  padding-bottom: $spacing-md;
}

.status-filter {
  background: #fff;
  padding: $spacing-md 0;
  margin-bottom: $spacing-md;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);

  .status-scroll {
    white-space: nowrap;
    padding: 0 $spacing-md;

    .status-item {
      display: inline-block;
      padding: $spacing-xs $spacing-lg;
      margin-right: $spacing-sm;
      border-radius: $radius-full;
      font-size: $font-size-xs;
      background: #f1f5f9;
      color: var(--text-secondary);
      transition: all 0.2s;

      &.active {
        background: $gradient-brand;
        color: white;
        box-shadow: 0 4rpx 12rpx rgba(74, 108, 247, 0.3);
      }
    }
  }
}

.loading,
.empty {
  text-align: center;
  padding: $spacing-2xl 0;
  color: var(--text-tertiary);
  background: #fff;
  margin: 0 $spacing-md;
  border-radius: $radius-lg;
}

.orders-list {
  padding: 0 $spacing-md;

  .order-item {
    background: #fff;
    border-radius: $radius-lg;
    overflow: hidden;
    margin-bottom: $spacing-md;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: $spacing-md;
      background: #f8fafc;
      border-bottom: 1rpx solid #e5e7eb;

      .order-number {
        font-size: $font-size-xs;
        color: var(--text-tertiary);
      }

      .order-status {
        font-size: $font-size-xs;
        padding: $spacing-xs $spacing-sm;
        border-radius: $radius-sm;
        font-weight: 500;

        &.status-pending {
          background: rgba(255, 180, 67, 0.15);
          color: #d97706;
        }

        &.status-completed {
          background: rgba(0, 196, 140, 0.15);
          color: #059669;
        }

        &.status-cancelled,
        &.status-refunded {
          background: #f1f5f9;
          color: #94a3b8;
        }
      }
    }

    .order-content {
      display: flex;
      padding: $spacing-md;
      background: #fff;

      .product-image {
        width: 140rpx;
        height: 140rpx;
        border-radius: $radius-md;
        flex-shrink: 0;
        background: #f1f5f9;

        &.placeholder {
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 50rpx;
        }
      }

      .product-info {
        flex: 1;
        padding: 0 $spacing-md;
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        .product-name {
          font-size: $font-size-sm;
          font-weight: $font-weight-bold;
          color: var(--text-primary);
        }

        .order-time {
          font-size: $font-size-xs;
          color: #94a3b8;
        }
      }

      .order-points {
        text-align: right;
        display: flex;
        flex-direction: column;
        align-items: flex-end;

        .points {
          display: block;
          font-size: $font-size-base;
          font-weight: $font-weight-bold;
          color: $brand-primary;
        }

        .label {
          font-size: $font-size-xs;
          color: #94a3b8;
        }

        .cash-amount {
          display: block;
          font-size: $font-size-sm;
          color: $semantic-error;
          margin-top: 4rpx;
        }
      }
    }

    .order-actions {
      padding: $spacing-sm $spacing-md;
      border-top: 1rpx solid #f1f5f9;
      background: #fafbfc;

      .cancel-btn {
        width: 100%;
        background: #fff;
        color: #64748b;
        border: 1rpx solid #e2e8f0;
        border-radius: $radius-sm;
        padding: $spacing-sm;
        font-size: $font-size-xs;

        &::after {
          border: none;
        }

        &:active {
          background: #f8fafc;
        }
      }
    }
  }
}
</style>
