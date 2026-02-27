<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listSalary } from '@/api/salary'
import { listPayday } from '@/api/payday'
import { useUserStore } from '@/stores/user'
import { useAbilityPointsStore } from '@/stores/ability-points'
import { useNotificationUnread } from '@/composables/useNotificationUnread'
import GlassTabBar from '@/components/GlassTabBar.vue'

const userStore = useUserStore()
const pointsStore = useAbilityPointsStore()

const loading = ref(true)
const { unreadCount: notificationUnread, startPolling } = useNotificationUnread()
const errMsg = ref('')
const recordList = ref([])
const paydayList = ref([])

// 用户信息
const userInfo = computed(() => userStore.userInfo)

// 用户剩余积分
const availablePoints = computed(() => pointsStore.availablePoints || 0)

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

  // 获取用户信息（强制刷新，不使用缓存）
  try {
    await userStore.fetchCurrentUser()
  } catch (e) {
    console.warn('[profile] Failed to fetch user info:', e)
  }

  // 获取积分信息 (Sprint 4.6)
  try {
    await pointsStore.fetchMyPoints()
  } catch (e) {
    console.warn('[profile] Failed to fetch points:', e)
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

// Sprint 4.2-4.6 新功能入口
function goYearEndBonus() {
  uni.navigateTo({ url: '/pages/year-end-bonus/index' })
}

function goSavingsGoals() {
  uni.navigateTo({ url: '/pages/savings-goals/index' })
}

function goAbilityPoints() {
  uni.navigateTo({ url: '/pages/ability-points/index' })
}

function goPointMall() {
  uni.navigateTo({ url: '/pages/point-mall/index' })
}

function goInviteCode() {
  uni.navigateTo({ url: '/pages/invite-code/index' })
}

function goExpenseTracking() {
  // 跳转到工资记录列表，用户可以在那里选择记录后添加支出
  uni.showToast({
    title: '请选择工资记录',
    icon: 'none',
  })
  uni.navigateTo({ url: '/pages/salary-record/index' })
}

// 生成海报
function generatePoster(recordId: string) {
  uni.navigateTo({ url: `/pages/poster/index?recordId=${recordId}` })
}

onMounted(load)
</script>

<template>
  <view class="page">
    <!-- 用户头部卡片 -->
    <view class="user-header">
      <view class="header-top">
        <view class="user-info-left" @click="goProfileEdit">
          <image class="user-avatar" :src="avatarUrl" mode="aspectFill" />
          <view class="user-text">
            <text class="user-name">{{ displayName }}</text>
            <view class="user-points-inline">
              <text class="points-value">{{ availablePoints }}</text>
              <text class="points-label">积分</text>
            </view>
          </view>
        </view>
        <view class="header-actions">
          <view class="msg-icon" @click="goNotification">
            <text class="icon-bell">🔔</text>
            <text v-if="notificationUnread > 0" class="msg-badge">{{
              notificationUnread > 99 ? '99+' : notificationUnread
            }}</text>
          </view>
          <view class="setting-icon" @click="goSettings">
            <text>⚙️</text>
          </view>
        </view>
      </view>
      <view v-if="userInfo?.phone_number" class="user-phone-row">
        <text class="phone-icon">📱</text>
        <text class="phone-number">{{ userInfo.phone_number }}</text>
        <text v-if="userInfo.phone_verified" class="verified-badge">✓ 已验证</text>
      </view>
    </view>

    <!-- 统计摘要 -->
    <view class="summary-row">
      <view class="summary-item" @click="goSalaryRecord">
        <text class="summary-num">{{ recordList.length }}</text>
        <text class="summary-label">发薪次数</text>
      </view>
      <view class="summary-item" @click="goPaydaySetting">
        <text class="summary-num">{{ paydayList.length }}</text>
        <text class="summary-label">发薪日配置</text>
      </view>
    </view>

    <!-- 常用功能 - 统一样式 -->
    <view class="section-card">
      <view class="section-title">常用功能</view>
      <view class="feature-grid-main">
        <view class="feature-card-main" @click="goSalaryRecord">
          <view class="feature-icon-main bg-blue">💵</view>
          <text class="feature-name-main">记工资</text>
        </view>
        <view class="feature-card-main" @click="goPaydaySetting">
          <view class="feature-icon-main bg-purple">📅</view>
          <text class="feature-name-main">发薪日设置</text>
        </view>
      </view>
    </view>

    <!-- 更多功能 - 统一在一个卡片中 -->
    <view class="section-card">
      <view class="section-title">更多功能</view>
      <view class="feature-grid">
        <view class="feature-item" @click="goCheckIn">
          <view class="feature-icon">✅</view>
          <text class="feature-name">每日签到</text>
        </view>
        <view class="feature-item" @click="goAbilityPoints">
          <view class="feature-icon">⭐</view>
          <text class="feature-name">我的积分</text>
        </view>
        <view class="feature-item" @click="goPointMall">
          <view class="feature-icon">🛒</view>
          <text class="feature-name">积分商城</text>
        </view>
        <view class="feature-item" @click="goSavingsGoals">
          <view class="feature-icon">💰</view>
          <text class="feature-name">存款目标</text>
        </view>
        <view class="feature-item" @click="goYearEndBonus">
          <view class="feature-icon">🎊</view>
          <text class="feature-name">年终奖</text>
        </view>
        <view class="feature-item" @click="goExpenseTracking">
          <view class="feature-icon">📊</view>
          <text class="feature-name">支出记录</text>
        </view>
        <view class="feature-item" @click="goInviteCode">
          <view class="feature-icon">✨</view>
          <text class="feature-name">邀请好友</text>
        </view>
      </view>
    </view>

    <!-- 最近记录 -->
    <view class="section-card">
      <text class="section-title">最近记录</text>
      <view v-if="loading" class="loading">加载中...</view>
      <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
      <view v-else-if="recordList.length === 0" class="empty">暂无记录</view>
      <view v-else class="list">
        <view
          v-for="item in recordList"
          :key="item.id"
          class="record-card"
          @click="generatePoster(item.id)"
        >
          <view class="card-content">
            <text class="amount">{{ item.amount }} 元</text>
            <text class="meta">{{ item.payday_date }} · {{ jobName(item.config_id) }}</text>
          </view>
          <view class="poster-btn">
            <text class="poster-icon">📄</text>
            <text class="poster-text">海报</text>
          </view>
        </view>
      </view>
    </view>

    <!-- TabBar 占位 -->
    <view class="tabbar-placeholder" />

    <!-- 液态玻璃 TabBar -->
    <GlassTabBar />
  </view>
</template>

<style scoped lang="scss">
.page {
  padding: 0 24rpx calc(24rpx + env(safe-area-inset-bottom));
  padding-top: calc(24rpx + env(safe-area-inset-top));
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #ffffff 100%);
}

// 用户头部卡片
.user-header {
  background: $gradient-brand;
  border-radius: 16rpx;
  padding: 32rpx 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(74, 108, 247, 0.25);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.user-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  border: 3rpx solid rgba(255, 255, 255, 0.4);
}

.user-text {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.user-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.user-points-inline {
  display: flex;
  align-items: baseline;
  gap: 6rpx;
}

.points-value {
  font-size: 28rpx;
  font-weight: 700;
  color: $accent-gold;
}

.points-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.msg-icon,
.setting-icon {
  position: relative;
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  font-size: 32rpx;
}

.msg-badge {
  position: absolute;
  top: -4rpx;
  right: -4rpx;
  background: $semantic-error;
  color: #fff;
  font-size: 18rpx;
  padding: 2rpx 8rpx;
  border-radius: 16rpx;
  min-width: 28rpx;
  text-align: center;
  font-weight: 600;
}

.user-phone-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.15);
}

.phone-icon {
  font-size: 24rpx;
}

.phone-number {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.9);
}

.verified-badge {
  font-size: 20rpx;
  color: $semantic-success;
  margin-left: auto;
}

// 统计摘要
.summary-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.summary-item {
  flex: 1;
  background: #fff;
  padding: 24rpx;
  text-align: center;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.summary-num {
  font-size: 40rpx;
  font-weight: 700;
  color: $brand-primary;
  display: block;
}

.summary-label {
  font-size: 24rpx;
  color: var(--text-tertiary);
  display: block;
  margin-top: 8rpx;
}

// 区块卡片
.section-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  display: block;
  margin-bottom: 20rpx;
}

// 常用功能 - 横向排列
.feature-grid-main {
  display: flex;
  gap: 20rpx;
}

.feature-card-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx 16rpx;
  background: #f8fafc;
  border-radius: 12rpx;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.feature-icon-main {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  font-size: 36rpx;

  &.bg-blue {
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  }

  &.bg-purple {
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  }
}

.feature-name-main {
  font-size: 26rpx;
  font-weight: 500;
  color: var(--text-primary);
}

// 更多功能 - 网格布局
.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24rpx 16rpx;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.95);
  }
}

.feature-icon {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 16rpx;
  font-size: 32rpx;
}

.feature-name {
  font-size: 24rpx;
  color: var(--text-secondary);
  text-align: center;
}

// 最近记录
.loading,
.err,
.empty {
  padding: 40rpx 0;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 26rpx;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx;
  background: #f8fafc;
  border-radius: 12rpx;
  transition: background 0.2s;

  &:active {
    background: #f1f5f9;
  }
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.amount {
  font-size: 32rpx;
  font-weight: 600;
  color: $semantic-success;
  display: block;
}

.meta {
  font-size: 24rpx;
  color: var(--text-tertiary);
  display: block;
  margin-top: 6rpx;
}

.poster-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12rpx 20rpx;
  background: $gradient-brand;
  border-radius: 10rpx;
  margin-left: 16rpx;
  min-width: 80rpx;
}

.poster-icon {
  font-size: 28rpx;
  margin-bottom: 4rpx;
}

.poster-text {
  font-size: 22rpx;
  color: #fff;
  font-weight: 500;
}

/* TabBar 占位 */
.tabbar-placeholder {
  height: calc(140rpx + env(safe-area-inset-bottom));
}
</style>
