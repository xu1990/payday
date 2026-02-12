<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listSalary, type SalaryRecord } from '@/api/salary'
import { listPayday, type PaydayConfig } from '@/api/payday'
import { getUnreadCount } from '@/api/notification'

const loading = ref(true)
const notificationUnread = ref(0)
const errMsg = ref('')
const recordList = ref<SalaryRecord[]>([])
const paydayList = ref<PaydayConfig[]>([])

async function load() {
  loading.value = true
  errMsg.value = ''
  try {
    const [records, paydays] = await Promise.all([
      listSalary({ limit: 20 }),
      listPayday(),
    ])
    recordList.value = Array.isArray(records) ? records : []
    paydayList.value = Array.isArray(paydays) ? paydays : []
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    recordList.value = []
    paydayList.value = []
  } finally {
    loading.value = false
  }
  try {
    const res = await getUnreadCount()
    notificationUnread.value = res?.unread_count ?? 0
  } catch {
    notificationUnread.value = 0
  }
}

function jobName(configId: string) {
  return paydayList.value.find((c) => c.id === configId)?.job_name ?? '—'
}

function goPaydaySetting() {
  uni.navigateTo({ url: '/pages/payday-setting/index' })
}

function goSalaryRecord() {
  uni.navigateTo({ url: '/pages/salary-record/index' })
}

function goPoster() {
  uni.navigateTo({ url: '/pages/poster/index' })
}

function goNotification() {
  uni.navigateTo({ url: '/pages/notification/list' })
}

function goSettings() {
  uni.navigateTo({ url: '/pages/settings/index' })
}

function goCheckIn() {
  uni.navigateTo({ url: '/pages/checkin/index' })
}

onMounted(load)
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">个人中心</text>
      <text class="tip">发薪记录与设置</text>
    </view>

    <view class="summary-row">
      <view class="summary-item">
        <text class="summary-num">{{ recordList.length }}</text>
        <text class="summary-label">发薪次数</text>
      </view>
      <view class="summary-item">
        <text class="summary-num">{{ paydayList.length }}</text>
        <text class="summary-label">发薪日配置</text>
      </view>
    </view>

    <view class="entry-row">
      <button class="btn-primary" @click="goSalaryRecord">记工资</button>
      <button class="btn-outline" @click="goPaydaySetting">发薪日设置</button>
      <button class="btn-outline" @click="goPoster">发薪海报</button>
    </view>
    <view class="entry-row entry-single">
      <view class="entry-item" @click="goNotification">
        <text class="entry-label">消息</text>
        <text v-if="notificationUnread > 0" class="badge">{{ notificationUnread > 99 ? '99+' : notificationUnread }}</text>
      </view>
    </view>

    <view class="section-title-alt">更多功能</view>
    <view class="entry-row">
      <button class="btn-outline" @click="goCheckIn">每日打卡</button>
      <button class="btn-outline" @click="goSettings">设置</button>
    </view>

    <view class="section">
      <text class="section-title">最近记录</text>
      <view v-if="loading" class="loading">加载中...</view>
      <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
      <view v-else-if="recordList.length === 0" class="empty">暂无记录</view>
      <view v-else class="list">
        <view v-for="item in recordList" :key="item.id" class="card">
          <text class="amount">{{ item.amount }} 元</text>
          <text class="meta">{{ item.payday_date }} · {{ jobName(item.config_id) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; min-height: 100vh; }
.head { margin-bottom: 24rpx; }
.title { font-size: 36rpx; font-weight: 600; display: block; }
.tip { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
.summary-row { display: flex; gap: 24rpx; margin-bottom: 24rpx; }
.summary-item {
  flex: 1;
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 24rpx;
  text-align: center;
}
.summary-num { font-size: 40rpx; font-weight: 600; color: #07c160; display: block; }
.summary-label { font-size: 24rpx; color: #666; display: block; margin-top: 8rpx; }
.entry-row { display: flex; gap: 20rpx; margin-bottom: 32rpx; }
.btn-primary { flex: 1; background: #07c160; color: #fff; border: none; border-radius: 8rpx; }
.btn-outline { flex: 1; background: #fff; color: #07c160; border: 1rpx solid #07c160; border-radius: 8rpx; }
.entry-single { margin-top: 0; }
.entry-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 8rpx;
}
.entry-label { font-size: 28rpx; color: #333; }
.badge {
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  padding: 0 8rpx;
  font-size: 22rpx;
  color: #fff;
  background: #e64340;
  border-radius: 16rpx;
  text-align: center;
}
.section { margin-top: 24rpx; }
.section-title { font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }
.section-title-alt { font-size: 28rpx; font-weight: 600; color: #666; display: block; margin: 24rpx 0 16rpx; }
.loading, .err, .empty { padding: 24rpx; text-align: center; color: #666; }
.err { color: #e64340; }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.card {
  background: #f8f8f8;
  border-radius: 12rpx;
  padding: 24rpx;
}
.amount { font-weight: 600; font-size: 30rpx; display: block; }
.meta { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
</style>
