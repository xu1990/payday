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
          <view class="transaction-desc">{{ item.description || item.transaction_type }}</view>
          <view class="transaction-time">{{ formatDateTime(item.created_at) }}</view>
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

const loading = ref(true)
const transactions = ref([])

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
    const token = uni.getStorageSync('token')

    const res = await uni.request({
      url: 'https://api.example.com/api/v1/ability-points/my/transactions',
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      transactions.value = res.data.data.transactions || []
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function getTransactionTitle(item) {
  if (item.transaction_type === 'earn' && item.event_type) {
    return transactionTitles[item.event_type] || item.event_type
  }
  return transactionTitles[item.transaction_type] || item.transaction_type
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
