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
      <view v-if="stats.my_bonus.records && stats.my_bonus.records.length > 0" class="my-bonus-list">
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
          <view class="range-item" v-for="(value, key) in stats.ranges" :key="key">
            <view class="range-label">{{ key }}</view>
            <view class="range-bar">
              <view class="bar-fill" :style="{ width: getPercentage(value, stats.total_count) + '%' }"></view>
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
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

function getPercentage(value, total) {
  if (total === 0) return 0
  return (value / total * 100).toFixed(1)
}

function goToAddBonus() {
  uni.navigateTo({ url: '/pages/salary-record/index?type=bonus' })
}
</script>

<style lang="scss" scoped>
.year-end-bonus-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
  padding: 40rpx;
  text-align: center;
  margin-bottom: 20rpx;

  .title {
    display: block;
    font-size: 36rpx;
    color: white;
    font-weight: bold;
    margin-bottom: 20rpx;
  }

  .year-picker {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.2);
    padding: 10rpx 30rpx;
    border-radius: 50rpx;
    color: white;

    .arrow {
      margin-left: 10rpx;
      font-size: 20rpx;
    }
  }
}

.action-bar {
  margin-bottom: 20rpx;

  .btn-add-bonus {
    width: 100%;
    background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
    color: white;
    border: none;
    border-radius: 50rpx;
    padding: 28rpx;
    font-size: 30rpx;
    font-weight: bold;
    box-shadow: 0 8rpx 24rpx rgba(253, 203, 110, 0.4);
  }
}

.my-bonus-card {
  background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(253, 203, 110, 0.3);

  &.empty-bonus {
    background: linear-gradient(135deg, #dfe6e9 0%, #b2bec3 100%);
  }

  .my-bonus-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;

    .my-bonus-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #2d3436;
    }

    .my-bonus-count {
      font-size: 24rpx;
      color: #636e72;
    }
  }

  .my-bonus-amount {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20rpx 0;
    border-top: 1rpx solid rgba(255, 255, 255, 0.3);

    .amount-label {
      font-size: 28rpx;
      color: #2d3436;
    }

    .amount-value {
      font-size: 48rpx;
      font-weight: bold;
      color: #d63031;
    }
  }

  .my-bonus-list {
    margin-top: 20rpx;
    border-top: 1rpx solid rgba(255, 255, 255, 0.3);
    padding-top: 20rpx;

    .bonus-record-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16rpx 0;
      border-bottom: 1rpx solid rgba(255, 255, 255, 0.2);

      &:last-child {
        border-bottom: none;
      }

      .record-amount {
        font-size: 28rpx;
        font-weight: bold;
        color: #2d3436;
      }

      .record-date {
        font-size: 24rpx;
        color: #636e72;
      }
    }
  }

  .empty-bonus-content {
    text-align: center;
    padding: 40rpx 0;

    .empty-icon {
      font-size: 80rpx;
      display: block;
      margin-bottom: 16rpx;
    }

    .empty-text {
      font-size: 28rpx;
      color: #2d3436;
      display: block;
      margin-bottom: 8rpx;
    }

    .empty-hint {
      font-size: 24rpx;
      color: #636e72;
      display: block;
    }
  }
}

.loading, .empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.stats-container {
  .overview-card {
    display: flex;
    background: white;
    border-radius: 20rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);

    .card-item {
      flex: 1;
      text-align: center;
      padding: 20rpx 0;

      &.highlight {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        border-radius: 15rpx;
        margin: 0 10rpx;
      }

      .label {
        display: block;
        font-size: 24rpx;
        color: #999;
        margin-bottom: 10rpx;
      }

      .value {
        font-size: 32rpx;
        font-weight: bold;
        color: #333;
      }
    }
  }

  .section {
    background: white;
    border-radius: 20rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;

    .section-title {
      font-size: 28rpx;
      font-weight: bold;
      margin-bottom: 20rpx;
      padding-bottom: 15rpx;
      border-bottom: 1rpx solid #eee;
    }
  }

  .range-bars {
    .range-item {
      display: flex;
      align-items: center;
      margin-bottom: 20rpx;

      .range-label {
        width: 100rpx;
        font-size: 24rpx;
      }

      .range-bar {
        flex: 1;
        height: 20rpx;
        background: #f0f0f0;
        border-radius: 10rpx;
        margin: 0 15rpx;
        overflow: hidden;

        .bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
          border-radius: 10rpx;
          transition: width 0.3s;
        }
      }

      .range-value {
        width: 80rpx;
        text-align: right;
        font-size: 24rpx;
        color: #666;
      }
    }
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .detail-label {
      font-size: 28rpx;
      color: #666;
    }

    .detail-value {
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
    }
  }
}
</style>
