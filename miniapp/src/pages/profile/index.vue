<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listSalary, type SalaryRecord } from '@/api/salary'
import { listPayday, type PaydayConfig } from '@/api/payday'
import { useUserStore } from '@/stores/user'
import { useNotificationUnread } from '@/composables/useNotificationUnread'

const userStore = useUserStore()

const loading = ref(true)
const { unreadCount: notificationUnread, startPolling } = useNotificationUnread()
const errMsg = ref('')
const recordList = ref<SalaryRecord[]>([])
const paydayList = ref<PaydayConfig[]>([])

// 用户信息
const userInfo = computed(() => userStore.userInfo)

// 显示名称：优先显示昵称，没有则显示匿名昵称
const displayName = computed(() => {
  return userInfo.value?.nickname || userInfo.value?.anonymous_name || '打工者'
})

// 头像：没有则使用默认头像
const avatarUrl = computed(() => {
  return userInfo.value?.avatar || '/static/default-avatar.png'
})

async function load() {
  loading.value = true
  errMsg.value = ''

  // 获取用户信息
  try {
    await userStore.fetchCurrentUser()
  } catch (e) {
    console.warn('[profile] Failed to fetch user info:', e)
  }

  try {
    const [records, paydays] = await Promise.all([listSalary({ limit: 20 }), listPayday()])
    recordList.value = Array.isArray(records) ? records : []
    paydayList.value = Array.isArray(paydays) ? paydays : []
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    recordList.value = []
    paydayList.value = []
  } finally {
    loading.value = false
  }

  // Start polling for notification unread count
  startPolling()
}

function jobName(configId: string) {
  return paydayList.value.find(c => c.id === configId)?.job_name ?? '—'
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

function goProfileEdit() {
  uni.navigateTo({ url: '/pages/profile-edit/index' })
}

onMounted(load)
</script>

<template>
  <view class="page">
    <!-- 用户头部 -->
    <view class="user-header" @click="goProfileEdit">
      <image class="user-avatar" :src="avatarUrl" mode="aspectFill" />
      <text class="user-name">{{ displayName }}</text>
    </view>

    <!-- 统计摘要 -->
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

    <!-- 操作按钮 -->
    <view class="entry-row">
      <button class="btn-primary" @click="goSalaryRecord">记工资</button>
      <button class="btn-outline" @click="goPaydaySetting">发薪日设置</button>
      <button class="btn-outline" @click="goPoster">发薪海报</button>
    </view>
    <view class="entry-row entry-single">
      <view class="entry-item" @click="goNotification">
        <text class="entry-label">消息</text>
        <text v-if="notificationUnread > 0" class="badge">{{
          notificationUnread > 99 ? '99+' : notificationUnread
        }}</text>
      </view>
    </view>

    <view class="section-title-alt">更多功能</view>
    <view class="entry-row">
      <button class="btn-outline" @click="goCheckIn">每日签到</button>
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

<style scoped lang="scss">
.page {
  padding: 24rpx;
  min-height: 100vh;
  background: #f5f5f5;
}

// 用户头部
.user-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 24rpx;
  margin-bottom: 24rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  background: rgba(255, 255, 255, 0.2);
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  margin-bottom: 16rpx;
}

.user-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.head {
  margin-bottom: 24rpx;
}
.title {
  font-size: 36rpx;
  font-weight: 600;
  display: block;
}
.tip {
  display: block;
  margin-top: 8rpx;
  color: #666;
  font-size: 26rpx;
}

.summary-row {
  display: flex;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.summary-item {
  flex: 1;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.summary-num {
  font-size: 40rpx;
  font-weight: 600;
  color: #667eea;
  display: block;
}

.summary-label {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-top: 8rpx;
}

.entry-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.btn-primary {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.btn-outline {
  flex: 1;
  background: #fff;
  color: #667eea;
  border: 1rpx solid #667eea;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.entry-single {
  margin-top: 0;
}

.entry-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 20rpx;
  background: #fff;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.entry-label {
  font-size: 28rpx;
  color: #333;
}

.badge {
  background: #ff4d4f;
  color: #fff;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  min-width: 32rpx;
  text-align: center;
}

.section-title-alt {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin: 24rpx 0 16rpx;
}

.section {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.loading,
.err,
.empty {
  padding: 40rpx 0;
  text-align: center;
  color: #999;
  font-size: 26rpx;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.card {
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 8rpx;
}

.amount {
  font-size: 32rpx;
  font-weight: 600;
  color: #07c160;
  display: block;
}

.meta {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-top: 8rpx;
}
</style>
