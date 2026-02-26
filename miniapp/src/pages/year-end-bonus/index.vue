<template>
  <view class="year-end-bonus-page">
    <view class="header">
      <text class="title">🎊 年终奖统计</text>
      <picker mode="selector" :range="years" :value="yearIndex" @change="onYearChange">
        <view class="year-picker">
          <text>{{ years[yearIndex] }}年</text>
          <text class="arrow">▼</text>
        </view>
      </picker>
    </view>

    <!-- 添加年终奖按钮 -->
    <view class="action-bar">
      <button class="btn-add-bonus" @click="goToAddBonus">+ 记录年终奖</button>
    </view>

    <!-- 我的年终奖 -->
    <view v-if="stats && stats.my_bonus" class="my-bonus-card">
      <view class="my-bonus-header">
        <text class="my-bonus-title">🎁 我的年终奖</text>
        <text class="my-bonus-count">{{ stats.my_bonus.count }}条记录</text>
      </view>
      <view class="my-bonus-amount">
        <text class="amount-label">总计</text>
        <text class="amount-value">¥{{ stats.my_bonus.total_amount }}</text>
      </view>
      <view
        v-if="stats.my_bonus.records && stats.my_bonus.records.length > 0"
        class="my-bonus-list"
      >
        <view v-for="record in stats.my_bonus.records" :key="record.id" class="bonus-record-item">
          <text class="record-amount">¥{{ record.amount }}</text>
          <text class="record-date">{{ record.payday_date || '未知日期' }}</text>
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="my-bonus-card empty-bonus">
      <view class="empty-bonus-content">
        <text class="empty-icon">🎁</text>
        <text class="empty-text">还没有年终奖记录</text>
        <text class="empty-hint">点击上方按钮记录你的年终奖</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="stats" class="stats-container">
      <!-- 总览卡片 -->
      <view class="overview-card">
        <view class="card-item">
          <text class="label">记录数</text>
          <text class="value">{{ stats.total_count }}</text>
        </view>
        <view class="card-item highlight">
          <text class="label">平均年终奖</text>
          <text class="value">¥{{ stats.average_amount }}</text>
        </view>
        <view class="card-item">
          <text class="label">中位数</text>
          <text class="value">¥{{ stats.median_amount }}</text>
        </view>
      </view>

      <!-- 区间分布 -->
      <view class="section">
        <view class="section-title">金额区间分布</view>
        <view class="range-bars">
          <view v-for="(value, key) in stats.ranges" :key="key" class="range-item">
            <view class="range-label">{{ key }}</view>
            <view class="range-bar">
              <view
                class="bar-fill"
                :style="{ width: getPercentage(value, stats.total_count) + '%' }"
              ></view>
            </view>
            <view class="range-value">{{ value }}人</view>
          </view>
        </view>
      </view>

      <!-- 其他统计 -->
      <view class="section">
        <view class="section-title">统计详情</view>
        <view class="detail-row">
          <text class="detail-label">最高金额</text>
          <text class="detail-value">¥{{ stats.max_amount }}</text>
        </view>
        <view class="detail-row">
          <text class="detail-label">最低金额</text>
          <text class="detail-value">¥{{ stats.min_amount }}</text>
        </view>
        <view class="detail-row">
          <text class="detail-label">总金额</text>
          <text class="detail-value">¥{{ stats.total_amount }}</text>
        </view>
      </view>
    </view>

    <view v-else class="empty">
      <text>暂无数据</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getYearEndBonusStats } from '@/api/statistics'

const loading = ref(true)
const stats = ref(null)
const years = ref([])
const yearIndex = ref(0)

onLoad(() => {
  const currentYear = new Date().getFullYear()
  years.value = [currentYear, currentYear - 1, currentYear - 2, '全部']
  fetchStats()
})

function onYearChange(e) {
  yearIndex.value = e.detail.value
  fetchStats()
}

async function fetchStats() {
  try {
    loading.value = true
    const selectedYear = years.value[yearIndex.value]
    const year = selectedYear === '全部' ? undefined : selectedYear

    stats.value = await getYearEndBonusStats(year)
  } catch (error) {
    console.error('Failed to fetch year-end bonus stats:', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function getPercentage(value, total) {
  if (total === 0) return 0
  return ((value / total) * 100).toFixed(1)
}

function goToAddBonus() {
  uni.navigateTo({ url: '/pages/salary-record/index?type=bonus' })
}
</script>

<style lang="scss" scoped>
.year-end-bonus-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding: $spacing-sm;
}

.header {
  background: $gradient-brand;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  text-align: center;
  margin-bottom: $spacing-sm;

  .title {
    display: block;
    font-size: $font-size-xl;
    color: white;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-sm;
  }

  .year-picker {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.2);
    padding: $spacing-xs $spacing-md;
    border-radius: $radius-xl;
    color: white;

    .arrow {
      margin-left: $spacing-xs;
      font-size: $font-size-xs;
    }
  }
}

.action-bar {
  margin-bottom: $spacing-sm;

  .btn-add-bonus {
    width: 100%;
    background: $semantic-warning;
    color: white;
    border: none;
    border-radius: $radius-xl;
    padding: $spacing-md;
    font-size: $font-size-base;
    font-weight: $font-weight-bold;
    box-shadow: $shadow-md;
  }
}

.my-bonus-card {
  @include glass-card();
  background: $semantic-warning;
  border-radius: $radius-lg;
  padding: $spacing-md;
  margin-bottom: $spacing-sm;
  box-shadow: $shadow-sm;

  &.empty-bonus {
    background: var(--bg-glass-subtle);
  }

  .my-bonus-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;

    .my-bonus-title {
      font-size: $font-size-lg;
      font-weight: $font-weight-bold;
      color: var(--text-primary);
    }

    .my-bonus-count {
      font-size: $font-size-xs;
      color: var(--text-secondary);
    }
  }

  .my-bonus-amount {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: $spacing-sm 0;
    border-top: 1rpx solid var(--border-subtle);

    .amount-label {
      font-size: $font-size-base;
      color: var(--text-primary);
    }

    .amount-value {
      font-size: $font-size-2xl;
      font-weight: $font-weight-bold;
      color: $semantic-error;
    }
  }

  .my-bonus-list {
    margin-top: $spacing-sm;
    border-top: 1rpx solid var(--border-subtle);
    padding-top: $spacing-sm;

    .bonus-record-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: $spacing-sm 0;
      border-bottom: 1rpx solid var(--border-subtle);

      &:last-child {
        border-bottom: none;
      }

      .record-amount {
        font-size: $font-size-base;
        font-weight: $font-weight-bold;
        color: var(--text-primary);
      }

      .record-date {
        font-size: $font-size-xs;
        color: var(--text-secondary);
      }
    }
  }

  .empty-bonus-content {
    text-align: center;
    padding: $spacing-lg 0;

    .empty-icon {
      font-size: 80rpx;
      display: block;
      margin-bottom: $spacing-sm;
    }

    .empty-text {
      font-size: $font-size-base;
      color: var(--text-primary);
      display: block;
      margin-bottom: $spacing-xs;
    }

    .empty-hint {
      font-size: $font-size-xs;
      color: var(--text-secondary);
      display: block;
    }
  }
}

.loading,
.empty {
  text-align: center;
  padding: 100rpx 0;
  color: var(--text-tertiary);
}

.stats-container {
  .overview-card {
    display: flex;
    @include glass-card();
    border-radius: $radius-lg;
    padding: $spacing-md;
    margin-bottom: $spacing-sm;
    box-shadow: $shadow-sm;

    .card-item {
      flex: 1;
      text-align: center;
      padding: $spacing-sm 0;

      &.highlight {
        background: $semantic-warning;
        border-radius: $radius-md;
        margin: 0 $spacing-xs;
      }

      .label {
        display: block;
        font-size: $font-size-xs;
        color: var(--text-tertiary);
        margin-bottom: $spacing-xs;
      }

      .value {
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        color: var(--text-primary);
      }
    }
  }

  .section {
    @include glass-card();
    border-radius: $radius-lg;
    padding: $spacing-md;
    margin-bottom: $spacing-sm;

    .section-title {
      font-size: $font-size-base;
      font-weight: $font-weight-bold;
      margin-bottom: $spacing-sm;
      padding-bottom: $spacing-sm;
      border-bottom: 1rpx solid var(--border-subtle);
      color: var(--text-primary);
    }
  }

  .range-bars {
    .range-item {
      display: flex;
      align-items: center;
      margin-bottom: $spacing-sm;

      .range-label {
        width: 100rpx;
        font-size: $font-size-xs;
        color: var(--text-secondary);
      }

      .range-bar {
        flex: 1;
        height: 20rpx;
        background: var(--bg-glass-subtle);
        border-radius: $radius-sm;
        margin: 0 $spacing-sm;
        overflow: hidden;

        .bar-fill {
          height: 100%;
          background: $gradient-brand;
          border-radius: $radius-sm;
          transition: width 0.3s;
        }
      }

      .range-value {
        width: 80rpx;
        text-align: right;
        font-size: $font-size-xs;
        color: var(--text-secondary);
      }
    }
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: $spacing-sm 0;
    border-bottom: 1rpx solid var(--border-subtle);

    &:last-child {
      border-bottom: none;
    }

    .detail-label {
      font-size: $font-size-base;
      color: var(--text-secondary);
    }

    .detail-value {
      font-size: $font-size-base;
      font-weight: $font-weight-bold;
      color: var(--text-primary);
    }
  }
}
</style>
