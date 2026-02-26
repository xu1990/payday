<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSummary, getTrend } from '@/api/statistics'

const loading = ref(true)
const errMsg = ref('')
const summary = ref(null)
const trendList = ref([])

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

function monthLabel(item) {
  return `${item.year}年${item.month}月`
}

function goInsights() {
  uni.navigateTo({ url: '/pages/insights/index' })
}

onMounted(load)
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">工资统计</text>
      <text class="tip">本月收入与近 6 月趋势</text>
      <button class="btn-link" @click="goInsights">数据洞察 →</button>
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

<style lang="scss" scoped>
.page {
  padding: $spacing-md;
  min-height: 100vh;
  background: var(--bg-base);
}
.head {
  margin-bottom: $spacing-md;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.title {
  font-size: $font-size-xl;
  font-weight: $font-weight-semibold;
  display: block;
}
.tip {
  display: block;
  margin-top: $spacing-xs;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}
.btn-link {
  padding: 0;
  margin-top: $spacing-xs;
  background: none;
  border: none;
  color: $brand-secondary;
  font-size: $font-size-sm;
}
.loading,
.err {
  padding: $spacing-xl;
  text-align: center;
  color: var(--text-secondary);
}
.err {
  color: $semantic-error;
}
.summary-card {
  background: $gradient-brand;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  color: #fff;
  margin-bottom: $spacing-lg;
}
.summary-label {
  font-size: $font-size-sm;
  opacity: 0.9;
  display: block;
}
.summary-amount {
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  display: block;
  margin-top: $spacing-xs;
}
.summary-meta {
  font-size: $font-size-sm;
  opacity: 0.85;
  display: block;
  margin-top: $spacing-xs;
}
.trend-section {
  margin-top: $spacing-md;
}
.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  display: block;
  margin-bottom: $spacing-sm;
}
.empty {
  padding: $spacing-md;
  color: var(--text-tertiary);
  font-size: $font-size-base;
}
.trend-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}
.trend-item {
  @include glass-card();
  padding: $spacing-md;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.trend-month {
  font-size: $font-size-base;
  color: var(--text-primary);
}
.trend-amount {
  font-weight: $font-weight-semibold;
  font-size: $font-size-lg;
  color: $brand-secondary;
}
.trend-count {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}
</style>
