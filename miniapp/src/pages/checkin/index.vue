<template>
  <view class="checkin-page">
    <view class="header">
      <text class="title">每日签到</text>
      <text class="subtitle">记录你的打工生活</text>
    </view>

    <!-- 签到统计卡片 -->
    <view class="stats-card">
      <view class="stat-item">
        <text class="stat-value">{{ stats.total_days }}</text>
        <text class="stat-label">累计签到</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ stats.this_month }}</text>
        <text class="stat-label">本月签到</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ stats.current_streak }}</text>
        <text class="stat-label">连续签到</text>
      </view>
    </view>

    <!-- 今日签到 -->
    <view class="today-section">
      <view class="today-title">今日签到</view>
      <button class="checkin-btn" :class="{ checked: todayChecked }" @click="handleCheckIn">
        <text v-if="todayChecked">已签到</text>
        <text v-else>签到</text>
      </button>
      <input v-model="note" class="note-input" placeholder="写点什么..." :disabled="todayChecked" />
    </view>

    <!-- 签到日历 -->
    <view class="calendar-section">
      <view class="calendar-header">
        <text @click="prevMonth">◀</text>
        <text class="calendar-title">{{ currentYear }}年{{ currentMonth }}月</text>
        <text @click="nextMonth">▶</text>
      </view>
      <view class="calendar-weekdays">
        <text v-for="day in weekdays" :key="day">{{ day }}</text>
      </view>
      <view class="calendar-days">
        <view
          v-for="(day, index) in calendarDays"
          :key="index"
          class="calendar-day"
          :class="{
            empty: !day.day,
            checked: day.checked,
            today: day.isToday,
          }"
        >
          <text v-if="day.day">{{ day.day }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getCheckInStats,
  getCheckInCalendar,
  createCheckIn,
  type CalendarItem,
} from '@/api/checkin'

const stats = ref({
  total_days: 0,
  this_month: 0,
  current_streak: 0,
})

const note = ref('')
const calendar = ref([])
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const todayChecked = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return calendar.value.find(item => item.date === today)?.checked
})

const calendarDays = computed(() => {
  const days: Array<{ day?: number; checked?: boolean; isToday?: boolean }> = []
  const firstDay = new Date(currentYear.value, currentMonth.value - 1, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value, 0)
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  // 空白填充
  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push({})
  }

  // 日期填充
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const item = calendar.value.find(c => c.date === dateStr)
    const isToday = dateStr === todayStr
    days.push({
      day: d,
      checked: item?.checked,
      isToday,
    })
  }

  return days
})

const loadStats = async () => {
  try {
    stats.value = await getCheckInStats()
  } catch (error) {
    // Failed to load stats
  }
}

const loadCalendar = async () => {
  try {
    const res = await getCheckInCalendar(currentYear.value, currentMonth.value)
    calendar.value = res.items
  } catch (error) {
    // Failed to load calendar
  }
}

const handleCheckIn = async () => {
  if (todayChecked.value) {
    uni.showToast({ title: '今天已签到', icon: 'none' })
    return
  }

  try {
    const today = new Date().toISOString().split('T')[0]
    await createCheckIn({
      check_date: today,
      note: note.value || undefined,
    })
    uni.showToast({ title: '签到成功', icon: 'success' })
    note.value = ''
    await loadStats()
    await loadCalendar()
  } catch (error) {
    uni.showToast({ title: '签到失败', icon: 'none' })
  }
}

const prevMonth = () => {
  if (currentMonth.value === 1) {
    currentYear.value--
    currentMonth.value = 12
  } else {
    currentMonth.value--
  }
  loadCalendar()
}

const nextMonth = () => {
  if (currentMonth.value === 12) {
    currentYear.value++
    currentMonth.value = 1
  } else {
    currentMonth.value++
  }
  loadCalendar()
}

onMounted(() => {
  loadStats()
  loadCalendar()
})
</script>

<style lang="scss" scoped>
.checkin-page {
  padding: $spacing-md;
  background: var(--bg-base);
  min-height: 100vh;
}

.header {
  margin-bottom: $spacing-lg;
}

.title {
  font-size: $font-size-display;
  font-weight: $font-weight-bold;
  display: block;
}

.subtitle {
  font-size: $font-size-base;
  color: var(--text-secondary);
  display: block;
  margin-top: $spacing-xs;
}

.stats-card {
  @include glass-card();
  display: flex;
  justify-content: space-around;
  background: var(--bg-glass-subtle);
  border-radius: $radius-lg;
  padding: $spacing-xl $spacing-md;
  margin-bottom: $spacing-lg;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: $font-size-3xl;
  font-weight: $font-weight-bold;
  color: $brand-primary;
  display: block;
}

.stat-label {
  font-size: $font-size-sm;
  color: var(--text-secondary);
  margin-top: $spacing-xs;
  display: block;
}

.today-section {
  @include glass-card();
  background: var(--bg-glass-subtle);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.today-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  margin-bottom: $spacing-md;
}

.checkin-btn {
  width: 100%;
  height: 100rpx;
  background: $brand-primary;
  color: #fff;
  font-size: $font-size-xl;
  border-radius: $radius-lg;
  border: none;
  margin-bottom: $spacing-md;
}

.checkin-btn.checked {
  background: var(--text-tertiary);
}

.note-input {
  @include glass-input();
  width: 100%;
  padding: $spacing-md;
  border: 2rpx solid var(--border-subtle);
  border-radius: $radius-md;
  font-size: $font-size-base;
}

.calendar-section {
  @include glass-card();
  background: var(--bg-glass-subtle);
  border-radius: $radius-lg;
  padding: $spacing-lg;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-md;
}

.calendar-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
}

.calendar-weekdays {
  display: flex;
  margin-bottom: $spacing-xs;
}

.calendar-weekdays text {
  flex: 1;
  text-align: center;
  font-size: $font-size-sm;
  color: var(--text-secondary);
  padding: $spacing-xs 0;
}

.calendar-days {
  display: flex;
  flex-wrap: wrap;
}

.calendar-day {
  width: 14.28%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-base;
  border-radius: $radius-xs;
  margin-bottom: $spacing-xs;
}

.calendar-day.empty {
  pointer-events: none;
}

.calendar-day.checked {
  background: $brand-primary;
  color: #fff;
}

.calendar-day.today {
  border: 2rpx solid $brand-primary;
}
</style>
