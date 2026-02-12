<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import AppFooter from '@/components/AppFooter.vue'
import AppLogos from '@/components/AppLogos.vue'
import InputEntry from '@/components/InputEntry.vue'
import { listPayday } from '@/api/payday'
import type { MoodType } from '@/api/salary'

const MOOD_STORAGE_KEY = 'payday_home_mood'
const moodOptions: { value: MoodType; label: string }[] = [
  { value: 'happy', label: '开心' },
  { value: 'relief', label: '续命' },
  { value: 'sad', label: '崩溃' },
  { value: 'expect', label: '期待' },
  { value: 'angry', label: '暴躁' },
]

/** 根据公历「每月 payday 日」算距离今天的天数，0 表示今天发薪 */
function daysToNextPayday(payday: number): number {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  const d = now.getDate()
  const thisMonthPay = new Date(y, m, Math.min(payday, new Date(y, m + 1, 0).getDate()))
  const today = new Date(y, m, d)
  if (today <= thisMonthPay) {
    return Math.round((thisMonthPay.getTime() - today.getTime()) / (24 * 60 * 60 * 1000))
  }
  const nextMonth = new Date(y, m + 1, 1)
  const nextPay = new Date(nextMonth.getFullYear(), nextMonth.getMonth(), Math.min(payday, new Date(nextMonth.getFullYear(), nextMonth.getMonth() + 1, 0).getDate()))
  return Math.round((nextPay.getTime() - today.getTime()) / (24 * 60 * 60 * 1000))
}

/** 本月进度：已过天数 / 总天数 */
function monthProgress(): { passed: number; total: number; ratio: number } {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  const passed = now.getDate()
  const total = new Date(y, m + 1, 0).getDate()
  return { passed, total, ratio: total > 0 ? Math.round((passed / total) * 100) : 0 }
}

const loading = ref(true)
const daysToPayday = ref<number | null>(null)
const hasPaydayConfig = ref(false)
const selectedMood = ref<MoodType>('happy')
const progress = ref(monthProgress())

onShow(() => {
  progress.value = monthProgress()
  try {
    const saved = uni.getStorageSync(MOOD_STORAGE_KEY) as MoodType | undefined
    if (saved && moodOptions.some((o) => o.value === saved)) selectedMood.value = saved
  } catch (_) {}
  loading.value = true
  listPayday()
    .then((list) => {
      const active = (list || []).filter((c) => c.is_active === 1)
      hasPaydayConfig.value = active.length > 0
      if (active.length === 0) {
        daysToPayday.value = null
        return
      }
      const solar = active.filter((c) => c.calendar_type === 'solar')
      const daysList = solar.length ? solar.map((c) => daysToNextPayday(c.payday)) : [999]
      daysToPayday.value = Math.min(...daysList)
    })
    .catch(() => {
      hasPaydayConfig.value = false
      daysToPayday.value = null
    })
    .finally(() => {
      loading.value = false
    })
})

function setMood(mood: MoodType) {
  selectedMood.value = mood
  try {
    uni.setStorageSync(MOOD_STORAGE_KEY, mood)
  } catch (_) {}
}

function goFeed() {
  uni.navigateTo({ url: '/pages/feed/index' })
}

function goPaydaySetting() {
  uni.navigateTo({ url: '/pages/payday-setting/index' })
}

function goSalaryRecord() {
  uni.navigateTo({ url: '/pages/salary-record/index' })
}

function goInsights() {
  uni.navigateTo({ url: '/pages/insights/index' })
}

function goMembership() {
  uni.navigateTo({ url: '/pages/membership/index' })
}

function goCheckIn() {
  uni.navigateTo({ url: '/pages/checkin/index' })
}
</script>

<template>
  <view class="root-container">
    <AppLogos />
    <view class="payday-card">
      <text class="payday-title">发薪状态</text>
      <text v-if="loading" class="payday-desc">加载中…</text>
      <template v-else-if="!hasPaydayConfig">
        <text class="payday-desc">未设置发薪日</text>
        <button class="btn-link" @click="goPaydaySetting">去设置</button>
      </template>
      <text v-else-if="daysToPayday === 0" class="payday-desc">今天发薪日</text>
      <text v-else class="payday-desc">距离下次发薪 {{ daysToPayday }} 天</text>
    </view>
    <view class="mood-section">
      <text class="section-title">今日心情</text>
      <view class="mood-row">
        <view
          v-for="opt in moodOptions"
          :key="opt.value"
          class="mood-item"
          :class="{ active: selectedMood === opt.value }"
          @click="setMood(opt.value)"
        >
          <text class="mood-label">{{ opt.label }}</text>
        </view>
      </view>
    </view>
    <view class="progress-section">
      <text class="section-title">本月进度</text>
      <view class="progress-bar">
        <view class="progress-inner" :style="{ width: progress.ratio + '%' }" />
      </view>
      <text class="progress-desc">{{ progress.passed }} / {{ progress.total }} 天</text>
    </view>
    <view class="entry-row">
      <button class="btn-primary" @click="goSalaryRecord">记工资</button>
      <button class="btn-secondary" @click="goPaydaySetting">设置发薪日</button>
    </view>
    <view class="entry-row">
      <button class="btn-outline" @click="goFeed">关注流</button>
    </view>

    <view class="entry-row">
      <button class="btn-secondary" @click="goCheckIn">每日打卡</button>
      <button class="btn-secondary" @click="goInsights">数据洞察</button>
    </view>

    <view class="entry-row">
      <button class="btn-outline" @click="goMembership">会员中心</button>
    </view>
    <InputEntry />
    <AppFooter />
  </view>
</template>

<style scoped>
.root-container {
  padding: 5rem 2.5rem;
  text-align: center;
}
.payday-card {
  margin: 1rem 0;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 8px;
}
.payday-title { font-weight: 600; display: block; }
.payday-desc { display: block; margin-top: 0.5rem; color: #666; }
.entry-row { margin: 1rem 0; }
.btn-primary { padding: 0.5rem 1.5rem; background: #07c160; color: #fff; border: none; border-radius: 8px; }
.btn-secondary { padding: 0.5rem 1.5rem; background: #576b95; color: #fff; border: none; border-radius: 8px; margin-left: 0.5rem; }
.btn-outline { padding: 0.5rem 1.5rem; background: transparent; color: #07c160; border: 1px solid #07c160; border-radius: 8px; }
.btn-link { margin-top: 0.5rem; padding: 0.25rem 0; background: none; border: none; color: #07c160; font-size: 0.9rem; }
.mood-section, .progress-section { margin: 1rem 0; text-align: left; }
.section-title { font-weight: 600; font-size: 0.95rem; display: block; margin-bottom: 0.5rem; }
.mood-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.mood-item { padding: 0.4rem 0.8rem; border-radius: 999px; border: 1px solid #ddd; background: #fff; }
.mood-item.active { border-color: #07c160; background: #e8f8f0; }
.mood-label { font-size: 0.9rem; }
.progress-bar { height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.progress-inner { height: 100%; background: #07c160; border-radius: 4px; transition: width 0.2s; }
.progress-desc { font-size: 0.85rem; color: #666; margin-top: 0.25rem; display: block; }
</style>
