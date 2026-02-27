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
      <view v-for="item in transactions" :key="item.id" class="transaction-item">
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
  refund: '退还积分',
}

onMounted(() => {
  fetchTransactions()
})

async function fetchTransactions() {
  try {
    loading.value = true
    error.value = null
    const response = await getMyTransactions()
    // 后端返回 snake_case 字段，前端需要映射到 camelCase
    transactions.value = (response.transactions || []).map(item => ({
      ...item,
      transactionType: item.transaction_type ?? item.transactionType,
      eventType: item.event_type ?? item.eventType,
      createdAt: item.created_at ?? item.createdAt,
      balanceAfter: item.balance_after ?? item.balanceAfter,
    }))
  } catch (err) {
    console.error('Failed to fetch transactions:', err)
    error.value = err.message || '加载失败'
    uni.showToast({
      title: error.value,
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function getTransactionTitle(item) {
  const transactionType = item.transaction_type ?? item.transactionType
  const eventType = item.event_type ?? item.eventType
  if (transactionType === 'earn' && eventType) {
    return transactionTitles[eventType] || eventType
  }
  return transactionTitles[transactionType] || transactionType
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
  background: var(--bg-base);
  padding: $spacing-md;
}

.header {
  text-align: center;
  padding: $spacing-lg 0;

  .title {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
  }
}

.loading,
.empty {
  text-align: center;
  padding: 100rpx 0;
  color: var(--text-secondary);

  .empty-icon {
    display: block;
    font-size: 80rpx;
    margin-bottom: $spacing-md;
  }

  .empty-text {
    font-size: $font-size-base;
  }
}

.transactions-list {
  .transaction-item {
    @include glass-card();
    display: flex;
    align-items: center;
    background: var(--bg-glass-subtle);
    border-radius: $radius-lg;
    padding: $spacing-md;
    margin-bottom: $spacing-sm;

    .transaction-icon {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: $font-size-2xl;
      font-weight: $font-weight-bold;
      margin-right: $spacing-md;

      &.earn {
        background: rgba($semantic-success, 0.1);
        color: $semantic-success;
      }

      &.spend {
        background: rgba($semantic-error, 0.1);
        color: $semantic-error;
      }
    }

    .transaction-info {
      flex: 1;

      .transaction-title {
        font-size: $font-size-base;
        font-weight: $font-weight-bold;
        margin-bottom: $spacing-xs;
      }

      .transaction-desc {
        font-size: $font-size-sm;
        color: var(--text-secondary);
        margin-bottom: $spacing-xs;
      }

      .transaction-time {
        font-size: $font-size-xs;
        color: var(--text-tertiary);
      }
    }

    .transaction-amount {
      font-size: $font-size-xl;
      font-weight: $font-weight-bold;

      &.earn {
        color: $semantic-success;
      }

      &.spend {
        color: $semantic-error;
      }
    }
  }
}
</style>
