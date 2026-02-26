<template>
  <view class="savings-goals-page">
    <view class="header">
      <text class="title">存款目标</text>
      <text class="subtitle">为实现梦想而储蓄</text>
    </view>

    <!-- 目标列表 -->
    <view class="goals-list">
      <view v-for="goal in goals" :key="goal.id" class="goal-card" @tap="viewGoal(goal.id)">
        <view class="goal-header">
          <view class="goal-title">
            <text v-if="goal.icon">{{ goal.icon }} </text>
            <text>{{ goal.title }}</text>
          </view>
          <view class="goal-status" :class="'status-' + goal.status">
            <text>{{ getStatusText(goal.status) }}</text>
          </view>
        </view>

        <view class="progress-section">
          <view class="progress-info">
            <text class="current">¥{{ goal.currentAmount }}</text>
            <text class="target">目标 ¥{{ goal.targetAmount }}</text>
          </view>
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: goal.progressPercentage + '%' }"></view>
          </view>
          <text class="progress-text">{{ goal.progressPercentage }}%</text>
        </view>

        <view class="goal-footer">
          <text class="remaining">还差 ¥{{ goal.remainingAmount }}</text>
          <view class="actions">
            <button class="deposit-btn" size="mini" @tap.stop="depositToGoal(goal.id)">存入</button>
          </view>
        </view>

        <view v-if="goal.deadline" class="goal-deadline">
          <text>截止：{{ formatDate(goal.deadline) }}</text>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="goals.length === 0 && !loading" class="empty">
      <text class="empty-icon">🎯</text>
      <text class="empty-text">还没有存款目标</text>
      <text class="empty-hint">创建一个目标，开始存钱吧</text>
    </view>

    <!-- 创建按钮 -->
    <view class="fab" @tap="createGoal">
      <text class="fab-icon">+</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getSavingsGoals, deleteSavingsGoal } from '@/api/savings'
import { transformSavingsGoals } from '@/utils/transform'

const loading = ref(true)
const goals = ref([])
const isInitialized = ref(false)

onMounted(() => {
  fetchGoals()
  isInitialized.value = true
})

// 每次页面显示时刷新列表（从创建/存款页返回时自动刷新）
onShow(() => {
  if (isInitialized.value) {
    fetchGoals()
  }
})

async function fetchGoals() {
  try {
    loading.value = true
    const res = await getSavingsGoals()
    if (res.goals) {
      goals.value = transformSavingsGoals(res.goals)
    }
  } catch (error) {
    console.error('Failed to fetch savings goals:', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function getStatusText(status) {
  const map = {
    active: '进行中',
    completed: '已完成',
    cancelled: '已取消',
    paused: '已暂停',
  }
  return map[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function viewGoal(id) {
  uni.navigateTo({
    url: `/pages/savings-goal-detail/index?id=${id}`,
  })
}

function depositToGoal(id) {
  uni.navigateTo({
    url: `/pages/savings-deposit/index?id=${id}`,
  })
}

function createGoal() {
  uni.navigateTo({
    url: '/pages/savings-goal-create/index',
  })
}

async function handleDelete(id, event) {
  event.stopPropagation()
  try {
    const res = await uni.showModal({
      title: '确认删除',
      content: '确定要删除这个存款目标吗？',
    })
    if (res.confirm) {
      await deleteSavingsGoal(id)
      uni.showToast({
        title: '删除成功',
        icon: 'success',
      })
      fetchGoals()
    }
  } catch (error) {
    console.error('Failed to delete savings goal:', error)
    uni.showToast({
      title: '删除失败，请重试',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.savings-goals-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding: $spacing-md;
  padding-bottom: 150rpx;
}

.header {
  text-align: center;
  padding: $spacing-xl 0;

  .title {
    display: block;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-xs;
    color: var(--text-primary);
  }

  .subtitle {
    font-size: $font-size-sm;
    color: var(--text-tertiary);
  }
}

.goals-list {
  .goal-card {
    @include glass-card();
    padding: $spacing-lg;
    margin-bottom: $spacing-md;

    .goal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-md;

      .goal-title {
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        color: var(--text-primary);
      }

      .goal-status {
        padding: 5rpx $spacing-sm;
        border-radius: $radius-xl;
        font-size: $font-size-xs;

        &.status-active {
          background: rgba($brand-primary, 0.1);
          color: $brand-primary;
        }

        &.status-completed {
          background: rgba($semantic-success, 0.1);
          color: $semantic-success;
        }

        &.status-cancelled {
          background: var(--bg-glass-subtle);
          color: var(--text-tertiary);
        }

        &.status-paused {
          background: rgba($semantic-warning, 0.1);
          color: $semantic-warning;
        }
      }
    }

    .progress-section {
      margin-bottom: $spacing-md;

      .progress-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: $spacing-xs;

        .current {
          font-size: $font-size-2xl;
          font-weight: $font-weight-bold;
          color: $brand-primary;
        }

        .target {
          font-size: $font-size-sm;
          color: var(--text-tertiary);
        }
      }

      .progress-bar {
        height: 16rpx;
        background: var(--bg-glass-subtle);
        border-radius: $radius-sm;
        overflow: hidden;
        margin-bottom: $spacing-xs;

        .progress-fill {
          height: 100%;
          background: $gradient-brand;
          border-radius: $radius-sm;
          transition: width 0.3s $ease-out;
        }
      }

      .progress-text {
        font-size: $font-size-sm;
        color: var(--text-secondary);
      }
    }

    .goal-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: $spacing-sm;
      border-top: 1rpx solid var(--border-subtle);

      .remaining {
        font-size: $font-size-sm;
        color: var(--text-secondary);
      }

      .deposit-btn {
        background: $brand-primary;
        color: white;
        border: none;
        border-radius: $radius-xl;
        padding: $spacing-xs $spacing-lg;
        font-size: $font-size-sm;
      }
    }

    .goal-deadline {
      margin-top: $spacing-sm;
      padding-top: $spacing-sm;
      border-top: 1rpx dashed var(--border-subtle);
      font-size: $font-size-sm;
      color: var(--text-tertiary);
    }
  }
}

.empty {
  text-align: center;
  padding: $spacing-3xl 0;

  .empty-icon {
    display: block;
    font-size: 80rpx;
    margin-bottom: $spacing-md;
  }

  .empty-text {
    display: block;
    font-size: $font-size-base;
    color: var(--text-primary);
    margin-bottom: $spacing-xs;
  }

  .empty-hint {
    font-size: $font-size-sm;
    color: var(--text-tertiary);
  }
}

.fab {
  position: fixed;
  right: $spacing-xl;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background: $gradient-brand;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-lg;

  .fab-icon {
    font-size: 50rpx;
    color: white;
    line-height: 1;
  }
}
</style>
