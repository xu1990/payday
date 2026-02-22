<template>
  <view class="savings-goals-page">
    <view class="header">
      <text class="title">💰 存款目标</text>
      <text class="subtitle">为实现梦想而储蓄</text>
    </view>

    <!-- 目标列表 -->
    <view class="goals-list">
      <view
        class="goal-card"
        v-for="goal in goals"
        :key="goal.id"
        @tap="viewGoal(goal.id)"
      >
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
            <text class="current">¥{{ goal.current_amount }}</text>
            <text class="target">目标 ¥{{ goal.target_amount }}</text>
          </view>
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: goal.progress_percentage + '%' }"></view>
          </view>
          <text class="progress-text">{{ goal.progress_percentage }}%</text>
        </view>

        <view class="goal-footer">
          <text class="remaining">还差 ¥{{ goal.remaining_amount }}</text>
          <view class="actions">
            <button class="deposit-btn" size="mini" @tap.stop="depositToGoal(goal.id)">存入</button>
          </view>
        </view>

        <view class="goal-deadline" v-if="goal.deadline">
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

const loading = ref(true)
const goals = ref([])

onMounted(() => {
  fetchGoals()
})

async function fetchGoals() {
  try {
    loading.value = true
    const token = uni.getStorageSync('token')

    const res = await uni.request({
      url: 'https://api.example.com/api/v1/savings-goals',
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      goals.value = res.data.data.goals || []
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function getStatusText(status) {
  const map = {
    active: '进行中',
    completed: '已完成',
    cancelled: '已取消',
    paused: '已暂停'
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
    url: `/pages/savings-goal-detail/index?id=${id}`
  })
}

function depositToGoal(id) {
  uni.navigateTo({
    url: `/pages/savings-deposit/index?id=${id}`
  })
}

function createGoal() {
  uni.navigateTo({
    url: '/pages/savings-goal-create/index'
  })
}
</script>

<style lang="scss" scoped>
.savings-goals-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
  padding-bottom: 150rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;

  .title {
    display: block;
    font-size: 36rpx;
    font-weight: bold;
    margin-bottom: 10rpx;
  }

  .subtitle {
    font-size: 24rpx;
    color: #999;
  }
}

.goals-list {
  .goal-card {
    background: white;
    border-radius: 20rpx;
    padding: 25rpx;
    margin-bottom: 20rpx;

    .goal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20rpx;

      .goal-title {
        font-size: 32rpx;
        font-weight: bold;
      }

      .goal-status {
        padding: 5rpx 15rpx;
        border-radius: 20rpx;
        font-size: 22rpx;

        &.status-active {
          background: #e6f7ff;
          color: #1890ff;
        }

        &.status-completed {
          background: #f6ffed;
          color: #52c41a;
        }

        &.status-cancelled {
          background: #f5f5f5;
          color: #999;
        }

        &.status-paused {
          background: #fff7e6;
          color: #fa8c16;
        }
      }
    }

    .progress-section {
      margin-bottom: 20rpx;

      .progress-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10rpx;

        .current {
          font-size: 36rpx;
          font-weight: bold;
          color: #1890ff;
        }

        .target {
          font-size: 24rpx;
          color: #999;
        }
      }

      .progress-bar {
        height: 16rpx;
        background: #f0f0f0;
        border-radius: 8rpx;
        overflow: hidden;
        margin-bottom: 10rpx;

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #1890ff 0%, #52c41a 100%);
          border-radius: 8rpx;
          transition: width 0.3s;
        }
      }

      .progress-text {
        font-size: 24rpx;
        color: #666;
      }
    }

    .goal-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 15rpx;
      border-top: 1rpx solid #f0f0f0;

      .remaining {
        font-size: 24rpx;
        color: #666;
      }

      .deposit-btn {
        background: #1890ff;
        color: white;
        border: none;
        border-radius: 30rpx;
        padding: 8rpx 25rpx;
        font-size: 24rpx;
      }
    }

    .goal-deadline {
      margin-top: 15rpt;
      padding-top: 15rpx;
      border-top: 1rpx dashed #eee;
      font-size: 24rpx;
      color: #999;
    }
  }
}

.empty {
  text-align: center;
  padding: 100rpx 0;

  .empty-icon {
    display: block;
    font-size: 80rpx;
    margin-bottom: 20rpx;
  }

  .empty-text {
    display: block;
    font-size: 28rpx;
    color: #333;
    margin-bottom: 10rpx;
  }

  .empty-hint {
    font-size: 24rpx;
    color: #999;
  }
}

.fab {
  position: fixed;
  right: 40rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(102, 126, 234, 0.4);

  .fab-icon {
    font-size: 50rpx;
    color: white;
    line-height: 1;
  }
}
</style>
