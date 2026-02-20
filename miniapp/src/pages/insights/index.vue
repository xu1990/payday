<template>
  <view class="insights-page">
    <view class="header">
      <text class="title">数据洞察</text>
      <text class="subtitle">了解行业薪资趋势</text>
    </view>

    <view class="section">
      <view class="section-title">行业工资分布</view>
      <view class="chart-container">
        <qiun-ucharts type="pie" :opts="industryOpts" :chart-data="industryData" :canvas2d="true" />
      </view>
    </view>

    <view class="section">
      <view class="section-title">城市工资对比</view>
      <view class="chart-container">
        <qiun-ucharts type="bar" :opts="cityOpts" :chart-data="cityData" :canvas2d="true" />
      </view>
    </view>

    <view class="section">
      <view class="section-title">工资区间分布</view>
      <view class="chart-container">
        <qiun-ucharts
          type="pie"
          :opts="salaryRangeOpts"
          :chart-data="salaryRangeData"
          :canvas2d="true"
        />
      </view>
    </view>

    <view class="section">
      <view class="section-title">发薪日分布</view>
      <view class="chart-container">
        <qiun-ucharts type="column" :opts="paydayOpts" :chart-data="paydayData" :canvas2d="true" />
      </view>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getInsights, type DistributionItem } from '@/api/insights'

const loading = ref(true)
const industryData = ref({ series: [] })
const cityData = ref({ series: [] })
const salaryRangeData = ref({ series: [] })
const paydayData = ref({ series: [] })

const industryOpts = ref({
  color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de'],
  padding: [5, 5, 5, 5],
  enableScroll: false,
  extra: {
    pie: {
      activeOpacity: 0.5,
      activeRadius: 10,
      offsetAngle: 0,
      labelWidth: 15,
      ringWidth: 30,
      border: true,
      borderWidth: 2,
      borderColor: '#FFFFFF',
    },
  },
})

const cityOpts = ref({
  color: ['#5470c6'],
  padding: [15, 15, 0, 5],
  enableScroll: false,
  legend: {},
  xAxis: {
    disableGrid: true,
  },
  yAxis: {
    data: [{ min: 0 }],
  },
  extra: {
    bar: {
      type: 'group',
      width: 30,
      meterBor: 1,
      meterColor: '#FFFFFF',
      activeBgColor: '#000000',
      activeBgOpacity: 0.08,
      categoryPadding: 10,
    },
  },
})

const salaryRangeOpts = ref({
  color: ['#fac858', '#ee6666', '#73c0de', '#5470c6', '#91cc75'],
  padding: [5, 5, 5, 5],
  enableScroll: false,
  extra: {
    pie: {
      activeOpacity: 0.5,
      activeRadius: 10,
      offsetAngle: 0,
      labelWidth: 15,
      ringWidth: 30,
      border: true,
      borderWidth: 2,
      borderColor: '#FFFFFF',
    },
  },
})

const paydayOpts = ref({
  color: ['#91cc75'],
  padding: [15, 15, 0, 5],
  enableScroll: false,
  xAxis: {
    disableGrid: true,
  },
  yAxis: {
    data: [{ min: 0 }],
  },
  extra: {
    column: {
      type: 'group',
      width: 30,
      activeBgColor: '#000000',
      activeBgOpacity: 0.08,
    },
  },
})

onMounted(async () => {
  try {
    const res = await getInsights()

    if (res.industry_distribution) {
      industryData.value = {
        series: [
          {
            data: res.industry_distribution.distribution.map((item: DistributionItem) => ({
              name: item.label,
              value: item.count,
            })),
          },
        ],
      }
    }

    if (res.city_distribution) {
      cityData.value = {
        categories: res.city_distribution.distribution.map((item: DistributionItem) => item.label),
        series: [
          {
            name: '用户数',
            data: res.city_distribution.distribution.map((item: DistributionItem) => item.count),
          },
        ],
      }
    }

    if (res.salary_range_distribution) {
      salaryRangeData.value = {
        series: [
          {
            data: res.salary_range_distribution.distribution.map((item: DistributionItem) => ({
              name: item.label,
              value: item.count,
            })),
          },
        ],
      }
    }

    if (res.payday_distribution) {
      paydayData.value = {
        categories: res.payday_distribution.distribution.map(
          (item: DistributionItem) => item.label
        ),
        series: [
          {
            name: '人数',
            data: res.payday_distribution.distribution.map((item: DistributionItem) => item.count),
          },
        ],
      }
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.insights-page {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  margin-bottom: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
}

.subtitle {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-top: 10rpx;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.chart-container {
  width: 100%;
  height: 400rpx;
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
