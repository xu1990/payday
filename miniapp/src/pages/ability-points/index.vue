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
  color: $semantic-warning;
}

.points-container {
  .points-card {
    @include glass-card();
    background: $gradient-brand;
    border-radius: $radius-xl;
    padding: $spacing-xl;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
    box-shadow: $shadow-lg;

    .points-info {
      text-align: left;

      .points-value {
        display: block;
        font-size: $font-size-display;
        font-weight: $font-weight-bold;
        color: white;
        line-height: 1;
        margin-bottom: $spacing-xs;
      }

      .points-label {
        font-size: $font-size-sm;
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
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        color: white;
      }
    }
  }

  .stats-grid {
    @include glass-card();
    display: flex;
    background: var(--bg-glass-subtle);
    border-radius: $radius-lg;
    padding: $spacing-lg;
    margin-bottom: $spacing-md;

    .stat-item {
      flex: 1;
      text-align: center;

      &:not(:last-child) {
        border-right: 1rpx solid var(--border-subtle);
      }

      .stat-value {
        display: block;
        font-size: $font-size-xl;
        font-weight: $font-weight-bold;
        color: var(--text-primary);
        margin-bottom: $spacing-xs;
      }

      .stat-label {
        font-size: $font-size-sm;
        color: var(--text-secondary);
      }
    }
  }

  .level-section {
    @include glass-card();
    background: var(--bg-glass-subtle);
    border-radius: $radius-lg;
    padding: $spacing-lg;
    margin-bottom: $spacing-md;

    .level-title {
      font-size: $font-size-base;
      font-weight: $font-weight-bold;
      margin-bottom: $spacing-md;
    }

    .level-progress {
      .progress-bar {
        height: 20rpx;
        background: var(--border-regular);
        border-radius: $radius-sm;
        overflow: hidden;
        margin-bottom: $spacing-sm;

        .progress-fill {
          height: 100%;
          background: $gradient-brand;
          border-radius: $radius-sm;
          transition: width 0.3s;
        }
      }

      .level-info {
        display: flex;
        justify-content: space-between;
        font-size: $font-size-sm;
        color: var(--text-secondary);
      }
    }
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;

    .action-btn {
      width: 100%;
      border: none;
      border-radius: $radius-full;
      padding: $spacing-lg;
      font-size: $font-size-base;
      font-weight: $font-weight-bold;

      &.primary {
        background: $gradient-brand;
        color: white;
      }

      &.secondary {
        background: $gradient-brand;
        color: white;
      }

      &.tertiary {
        background: var(--bg-glass-subtle);
        color: var(--text-primary);
        border: 1rpx solid var(--border-regular);
      }

      &.mall {
        background: $gradient-brand;
        color: white;
      }

      &.invite {
        background: $gradient-brand;
        color: white;
      }
    }
  }
}
</style>
