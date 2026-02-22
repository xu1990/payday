<template>
  <view class="point-history-page">
    <view class="header">
      <text class="title">📜 积分明细</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="transactions.length === 0" class="empty">
      <text class="empty-icon">📝</text>
      <text class="empty-text">暂无积分记录</text>
    </view>

    <view v-else class="transactions-list">
      <view
        class="transaction-item"
        v-for="item in transactions"
        :key="item.id"
      >
        <view class="transaction-icon" :class="{ earn: item.amount > 0, spend: item.amount < 0 }">
          <text v-if="item.amount > 0">+</text>
          <text v-else>-</text>
        </view>

        <view class="transaction-info">
          <view class="transaction-title">{{ getTransactionTitle(item) }}</view>
          <view class="transaction-desc">{{ item.description || item.transactionType }}</view>
          <view class="transaction-time">{{ formatDateTime(item.createdAt) }}</view>
        </view>

        <view class="transaction-amount" :class="{ earn: item.amount > 0, spend: item.amount < 0 }">
          <text>{{ item.amount > 0 ? '+' : '' }}{{ item.amount }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyTransactions } from '@/api/ability-points'

const loading = ref(true)
const transactions = ref([])
const error = ref(null)

const transactionTitles = {
  checkin: '打卡奖励',
  post: '发布帖子',
  like: '获得点赞',
  comment: '发表评论',
  follow: '关注用户',
  salary: '记录工资',
  first_salary: '第一笔工资',
  savings_goal: '存款目标',
  redeem: '积分兑换',
  refund: '退还积分'
}

onMounted(() => {
  fetchTransactions()
})

async function fetchTransactions() {
  try {
    loading.value = true
    error.value = null
    const response = await getMyTransactions()
    transactions.value = response.transactions || []
  } catch (err) {
    console.error('Failed to fetch transactions:', err)
    error.value = err.message || '加载失败'
    uni.showToast({
      title: error.value,
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

function getTransactionTitle(item) {
  if (item.transactionType === 'earn' && item.eventType) {
    return transactionTitles[item.eventType] || item.eventType
  }
  return transactionTitles[item.transactionType] || item.transactionType
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours().toString().padStart(2, '0')
  const minute = date.getMinutes().toString().padStart(2, '0')
  return `${month}月${day}日 ${hour}:${minute}`
}
</script>

<style lang="scss" scoped>
.point-history-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 30rpx 0;

  .title {
    font-size: 36rpx;
    font-weight: bold;
  }
}

.loading, .empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;

  .empty-icon {
    display: block;
    font-size: 80rpx;
    margin-bottom: 20rpx;
  }

  .empty-text {
    font-size: 28rpx;
  }
}

.transactions-list {
  .transaction-item {
    display: flex;
    align-items: center;
    background: white;
    border-radius: 20rpx;
    padding: 25rpx;
    margin-bottom: 15rpx;

    .transaction-icon {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 40rpx;
      font-weight: bold;
      margin-right: 20rpx;

      &.earn {
        background: #f6ffed;
        color: #52c41a;
      }

      &.spend {
        background: #fff1f0;
        color: #ff4d4f;
      }
    }

    .transaction-info {
      flex: 1;

      .transaction-title {
        font-size: 28rpx;
        font-weight: bold;
        margin-bottom: 5rpx;
      }

      .transaction-desc {
        font-size: 24rpx;
        color: #999;
        margin-bottom: 5rpx;
      }

      .transaction-time {
        font-size: 22rpx;
        color: #ccc;
      }
    }

    .transaction-amount {
      font-size: 36rpx;
      font-weight: bold;

      &.earn {
        color: #52c41a;
      }

      &.spend {
        color: #ff4d4f;
      }
    }
  }
}
</style>
