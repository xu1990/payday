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
          <text class="points-value">{{ points.availablePoints }}</text>
          <text class="points-label">可用积分</text>
        </view>
        <view class="level-badge">
          <text class="level">LV.{{ points.level }}</text>
        </view>
      </view>

      <!-- 统计信息 -->
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ points.totalEarned }}</text>
          <text class="stat-label">累计获得</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ points.totalSpent }}</text>
          <text class="stat-label">累计消费</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ points.totalPoints }}</text>
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
            <text>当前: {{ points.totalPoints }}分</text>
            <text>下一级: {{ nextLevelPoints }}分</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="actions">
        <button class="action-btn primary" @tap="goToEvents">
          <text>📋 赚积分</text>
        </button>
        <button class="action-btn mall" @tap="goToMall">
          <text>🛒 积分商城</text>
        </button>
        <button class="action-btn invite" @tap="goToInvite">
          <text>✨ 邀请好友</text>
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
import { getMyPoints } from '@/api/ability-points'
import { safeNumber } from '@/utils/transform'

// 积分系统常量
const POINTS_PER_LEVEL = 1000 // 每升1级所需的积分

const loading = ref(true)
const points = ref(null)
const error = ref(null)

const levelProgress = computed(() => {
  if (!points.value) return 0
  const totalPoints = safeNumber(points.value.totalPoints, 0)
  const currentLevelPoints = totalPoints % POINTS_PER_LEVEL
  return ((currentLevelPoints / POINTS_PER_LEVEL) * 100).toFixed(1)
})

const nextLevelPoints = computed(() => {
  if (!points.value) return POINTS_PER_LEVEL
  const totalPoints = safeNumber(points.value.totalPoints, 0)
  return (Math.floor(totalPoints / POINTS_PER_LEVEL) + 1) * POINTS_PER_LEVEL
})

onMounted(() => {
  fetchPoints()
})

async function fetchPoints() {
  try {
    loading.value = true
    error.value = null
    const data = await getMyPoints()
    // 确保 NaN 值被转换为 0
    points.value = {
      ...data,
      availablePoints: safeNumber(data.availablePoints, 0),
      totalEarned: safeNumber(data.totalEarned, 0),
      totalSpent: safeNumber(data.totalSpent, 0),
      totalPoints: safeNumber(data.totalPoints, 0),
      level: safeNumber(data.level, 1),
    }
  } catch (err) {
    console.error('Failed to fetch points:', err)
    error.value = err.message || '加载失败'
    uni.showToast({
      title: error.value,
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function goToEvents() {
  uni.navigateTo({
    url: '/pages/point-events/index',
  })
}

function goToMall() {
  uni.navigateTo({
    url: '/pages/point-mall/index',
  })
}

function goToInvite() {
  uni.navigateTo({
    url: '/pages/invite-code/index',
  })
}

function goToRedemptions() {
  uni.navigateTo({
    url: '/pages/point-redemptions/index',
  })
}

function goToHistory() {
  uni.navigateTo({
    url: '/pages/point-history/index',
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

.loading,
.empty {
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

      &.mall {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
      }

      &.invite {
        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
        color: white;
      }
    }
  }
}
</style>
