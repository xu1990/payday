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
import { getInsights } from '@/api/insights'

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
            data: res.industry_distribution.distribution.map((item) => ({
              name: item.label,
              value: item.count,
            })),
          },
        ],
      }
    }

    if (res.city_distribution) {
      cityData.value = {
        categories: res.city_distribution.distribution.map((item) => item.label),
        series: [
          {
            name: '用户数',
            data: res.city_distribution.distribution.map((item) => item.count),
          },
        ],
      }
    }

    if (res.salary_range_distribution) {
      salaryRangeData.value = {
        series: [
          {
            data: res.salary_range_distribution.distribution.map((item) => ({
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
          (item) => item.label
        ),
        series: [
          {
            name: '人数',
            data: res.payday_distribution.distribution.map((item) => item.count),
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

<style lang="scss" scoped>
.insights-page {
  padding: $spacing-md;
  background: var(--bg-base);
  min-height: 100vh;
}

.header {
  margin-bottom: $spacing-lg;
}

.title {
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  display: block;
}

.subtitle {
  font-size: $font-size-base;
  color: var(--text-secondary);
  display: block;
  margin-top: $spacing-xs;
}

.section {
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  margin-bottom: $spacing-md;
}

.chart-container {
  width: 100%;
  height: 400rpx;
}

.loading {
  text-align: center;
  padding: $spacing-xl;
  color: var(--text-tertiary);
}
</style>
