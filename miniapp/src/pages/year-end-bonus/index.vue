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
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

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
    const token = uni.getStorageSync('token')
    const year = years.value[yearIndex.value] === '全部' ? '' : years.value[yearIndex.value]

    let url = 'https://api.example.com/api/v1/statistics/year-end-bonus'
    if (year) {
      url += `?year=${year}`
    }

    const res = await uni.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      stats.value = res.data.data
    } else {
      uni.showToast({ title: '加载失败', icon: 'none' })
    }
  } catch (error) {
    uni.showToast({ title: '网络错误', icon: 'none' })
    console.error(error)
  } finally {
    loading.value = false
  }
}

function getPercentage(value, total) {
  if (total === 0) return 0
  return (value / total * 100).toFixed(1)
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
