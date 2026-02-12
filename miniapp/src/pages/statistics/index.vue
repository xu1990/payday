<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSummary, getTrend, type MonthSummary, type TrendItem } from '@/api/statistics'

const loading = ref(true)
const errMsg = ref('')
const summary = ref<MonthSummary | null>(null)
const trendList = ref<TrendItem[]>([])

function nowYearMonth() {
  const d = new Date()
  return { year: d.getFullYear(), month: d.getMonth() + 1 }
}

async function load() {
  loading.value = true
  errMsg.value = ''
  const { year, month } = nowYearMonth()
  try {
    const [s, t] = await Promise.all([getSummary(year, month), getTrend(6)])
    summary.value = s
    trendList.value = Array.isArray(t) ? t : []
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    summary.value = null
    trendList.value = []
  } finally {
    loading.value = false
  }
}

function monthLabel(item: TrendItem) {
  return `${item.year}年${item.month}月`
}

onMounted(load)
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">工资统计</text>
      <text class="tip">本月收入与近 6 月趋势</text>
    </view>

    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
    <template v-else>
      <view class="summary-card">
        <text class="summary-label">本月收入（元）</text>
        <text class="summary-amount">{{ summary?.total_amount ?? '—' }}</text>
        <text class="summary-meta">共 {{ summary?.record_count ?? 0 }} 笔</text>
      </view>
      <view class="trend-section">
        <text class="section-title">近 6 月</text>
        <view v-if="trendList.length === 0" class="empty">暂无趋势数据</view>
        <view v-else class="trend-list">
          <view v-for="(item, i) in trendList" :key="i" class="trend-item">
            <text class="trend-month">{{ monthLabel(item) }}</text>
            <text class="trend-amount">{{ item.total_amount }} 元</text>
            <text class="trend-count">{{ item.record_count }} 笔</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; min-height: 100vh; }
.head { margin-bottom: 24rpx; }
.title { font-size: 36rpx; font-weight: 600; display: block; }
.tip { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
.loading, .err { padding: 40rpx; text-align: center; color: #666; }
.err { color: #e64340; }
.summary-card {
  background: linear-gradient(135deg, #07c160 0%, #06ad56 100%);
  border-radius: 16rpx;
  padding: 32rpx;
  color: #fff;
  margin-bottom: 32rpx;
}
.summary-label { font-size: 26rpx; opacity: 0.9; display: block; }
.summary-amount { font-size: 48rpx; font-weight: 700; display: block; margin-top: 8rpx; }
.summary-meta { font-size: 24rpx; opacity: 0.85; display: block; margin-top: 8rpx; }
.trend-section { margin-top: 24rpx; }
.section-title { font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }
.empty { padding: 24rpx; color: #999; font-size: 28rpx; }
.trend-list { display: flex; flex-direction: column; gap: 16rpx; }
.trend-item {
  background: #f8f8f8;
  border-radius: 12rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.trend-month { font-size: 28rpx; color: #333; }
.trend-amount { font-weight: 600; font-size: 30rpx; color: #07c160; }
.trend-count { font-size: 24rpx; color: #999; }
</style>
