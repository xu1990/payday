<template>
  <view class="ability-points-page">
    <view class="header">
      <text class="title">⭐ 我的积分</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="points" class="points-container">
      <!-- 积分卡片 -->
      <view class="points-card">
        <view class="points-info">
          <text class="points-value">{{ points.available_points }}</text>
          <text class="points-label">可用积分</text>
        </view>
        <view class="level-badge">
          <text class="level">LV.{{ points.level }}</text>
        </view>
      </view>

      <!-- 统计信息 -->
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ points.total_earned }}</text>
          <text class="stat-label">累计获得</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ points.total_spent }}</text>
          <text class="stat-label">累计消费</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ points.total_points }}</text>
          <text class="stat-label">总积分</text>
        </view>
      </view>

      <!-- 等级进度 -->
      <view class="level-section">
        <view class="level-title">等级进度</view>
        <view class="level-progress">
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: levelProgress + '%' }"></view>
          </view>
          <view class="level-info">
            <text>当前: {{ points.total_points }}分</text>
            <text>下一级: {{ (Math.floor(points.total_points / 1000) + 1) * 1000 }}分</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="actions">
        <button class="action-btn primary" @tap="goToEvents">
          <text>📋 赚积分</text>
        </button>
        <button class="action-btn secondary" @tap="goToRedemptions">
          <text>🎁 兑换中心</text>
        </button>
        <button class="action-btn tertiary" @tap="goToHistory">
          <text>📜 积分明细</text>
        </button>
      </view>
    </view>

    <view v-else class="empty">
      <text>暂无积分数据</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading = ref(true)
const points = ref(null)

const levelProgress = computed(() => {
  if (!points.value) return 0
  const currentLevelPoints = points.value.total_points % 1000
  return (currentLevelPoints / 1000 * 100).toFixed(1)
})

onMounted(() => {
  fetchPoints()
})

async function fetchPoints() {
  try {
    loading.value = true
    const token = uni.getStorageSync('token')

    const res = await uni.request({
      url: 'https://api.example.com/api/v1/ability-points/my',
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      points.value = res.data.data
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function goToEvents() {
  uni.navigateTo({
    url: '/pages/point-events/index'
  })
}

function goToRedemptions() {
  uni.navigateTo({
    url: '/pages/point-redemptions/index'
  })
}

function goToHistory() {
  uni.navigateTo({
    url: '/pages/point-history/index'
  })
}
</script>

<style lang="scss" scoped>
.ability-points-page {
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
}

.points-container {
  .points-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 30rpx;
    padding: 50rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    box-shadow: 0 10rpx 30rpx rgba(102, 126, 234, 0.3);

    .points-info {
      text-align: left;

      .points-value {
        display: block;
        font-size: 72rpx;
        font-weight: bold;
        color: white;
        line-height: 1;
        margin-bottom: 10rpx;
      }

      .points-label {
        font-size: 24rpx;
        color: rgba(255, 255, 255, 0.8);
      }
    }

    .level-badge {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      width: 120rpx;
      height: 120rpx;
      display: flex;
      align-items: center;
      justify-content: center;

      .level {
        font-size: 32rpx;
        font-weight: bold;
        color: white;
      }
    }
  }

  .stats-grid {
    display: flex;
    background: white;
    border-radius: 20rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;

    .stat-item {
      flex: 1;
      text-align: center;

      &:not(:last-child) {
        border-right: 1rpx solid #f0f0f0;
      }

      .stat-value {
        display: block;
        font-size: 36rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 10rpx;
      }

      .stat-label {
        font-size: 24rpx;
        color: #999;
      }
    }
  }

  .level-section {
    background: white;
    border-radius: 20rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;

    .level-title {
      font-size: 28rpx;
      font-weight: bold;
      margin-bottom: 20rpx;
    }

    .level-progress {
      .progress-bar {
        height: 20rpx;
        background: #f0f0f0;
        border-radius: 10rpx;
        overflow: hidden;
        margin-bottom: 15rpx;

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #fbc531 0%, #e1b12c 100%);
          border-radius: 10rpx;
          transition: width 0.3s;
        }
      }

      .level-info {
        display: flex;
        justify-content: space-between;
        font-size: 24rpx;
        color: #666;
      }
    }
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 15rpx;

    .action-btn {
      width: 100%;
      border: none;
      border-radius: 50rpx;
      padding: 30rpx;
      font-size: 28rpx;
      font-weight: bold;

      &.primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      &.secondary {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        color: #333;
      }

      &.tertiary {
        background: white;
        color: #333;
        border: 1rpx solid #e0e0e0;
      }
    }
  }
}
</style>
