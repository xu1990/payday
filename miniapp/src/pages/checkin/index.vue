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
const calendar = ref<CalendarItem[]>([])
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

<style scoped>
.checkin-page {
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

.stats-card {
  display: flex;
  justify-content: space-around;
  background: #fff;
  border-radius: 16rpx;
  padding: 40rpx 20rpx;
  margin-bottom: 30rpx;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 56rpx;
  font-weight: bold;
  color: #5470c6;
  display: block;
}

.stat-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
  display: block;
}

.today-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.today-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.checkin-btn {
  width: 100%;
  height: 100rpx;
  background: #5470c6;
  color: #fff;
  font-size: 36rpx;
  border-radius: 16rpx;
  border: none;
  margin-bottom: 20rpx;
}

.checkin-btn.checked {
  background: #ccc;
}

.note-input {
  width: 100%;
  padding: 20rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  font-size: 28rpx;
}

.calendar-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.calendar-title {
  font-size: 32rpx;
  font-weight: bold;
}

.calendar-weekdays {
  display: flex;
  margin-bottom: 10rpx;
}

.calendar-weekdays text {
  flex: 1;
  text-align: center;
  font-size: 24rpx;
  color: #999;
  padding: 10rpx 0;
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
  font-size: 28rpx;
  border-radius: 8rpx;
  margin-bottom: 10rpx;
}

.calendar-day.empty {
  pointer-events: none;
}

.calendar-day.checked {
  background: #5470c6;
  color: #fff;
}

.calendar-day.today {
  border: 2rpx solid #5470c6;
}
</style>
