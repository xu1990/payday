<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow, onLaunch } from '@dcloudio/uni-app'
import GlassTabBar from '@/components/GlassTabBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import AppLogos from '@/components/AppLogos.vue'
import InputEntry from '@/components/InputEntry.vue'
import { listPayday } from '@/api/payday'
import { getPointProducts } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'
import { getActiveTopics } from '@/api/topic'
import type { MoodType } from '@/api/salary'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { handleQRCodeLaunch } from '@/utils/qrcode'

const MOOD_STORAGE_KEY = 'payday_home_mood'
const moodOptions: { value; label: string }[] = [
  { value: 'happy', label: '开心' },
  { value: 'relief', label: '续命' },
  { value: 'sad', label: '崩溃' },
  { value: 'expect', label: '期待' },
  { value: 'angry', label: '暴躁' },
]

// Stores
const authStore = useAuthStore()
const userStore = useUserStore()

// Handle QR code scan on launch
onLaunch((options: any) => {
  console.log('[index] onLaunch called with options:', options)
  if (options?.scene) {
    console.log('[index] Scene detected, handling QR code scan')
    handleQRCodeLaunch(options.scene)
  }
})

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
  const nextPay = new Date(
    nextMonth.getFullYear(),
    nextMonth.getMonth(),
    Math.min(payday, new Date(nextMonth.getFullYear(), nextMonth.getMonth() + 1, 0).getDate())
  )
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
const daysToPayday = ref(null)
const hasPaydayConfig = ref(false)
const selectedMood = ref('happy')
const progress = ref(monthProgress())

// 积分商品相关
const products = ref([])
const productsLoading = ref(false)

// 用户剩余积分
const availablePoints = ref(0)

// 热门话题
const topics = ref([])
const topicsLoading = ref(false)

// 快捷入口
const quickEntries = ref([
  { icon: '💰', label: '工资', action: 'goSalaryRecord' },
  { icon: '🎯', label: '存钱目标', action: 'goSavingGoal' },
  { icon: '💸', label: '支出记录', action: 'goExpenseRecord' },
  { icon: '🎁', label: '积分', action: 'goPointMall' },
])

// 计算属性：用户信息
const isLoggedIn = computed(() => authStore.isLoggedIn)
const userName = computed(() => userStore.anonymousName || '打工者')
const userAvatar = computed(() => userStore.avatar || '/static/default-avatar.png')

onShow(async () => {
  console.log('[index] onShow called')

  // 每次显示时更新进度
  progress.value = monthProgress()

  // 先初始化 auth store 以加载 token
  console.log('[index] Initializing auth store...')
  await authStore.init()
  console.log('[index] Auth store initialized, isLoggedIn:', isLoggedIn.value)

  // 然后检查登录状态
  if (isLoggedIn.value) {
    console.log('[index] User is logged in, loading data...')
    // 已登录，延迟加载数据以确保 token 可用
    setTimeout(() => {
      loadPaydayData()
      loadPointProducts()
      loadUserPoints()
    }, 300) // 增加延迟到 300ms
  } else {
    console.warn('[index] User not logged in')
  }

  // 加载热门话题（无需登录）
  loadTopics()
})

/**
 * 加载发薪日数据
 */
async function loadPaydayData() {
  try {
    loading.value = true

    // 尝试获取用户信息（如果还没获取过）
    if (!userStore.currentUser) {
      console.log('[index] Fetching current user...')
      try {
        await userStore.fetchCurrentUser()
        console.log('[index] User fetched successfully')
      } catch (e) {
        // 如果是401错误，说明token失效，不应该继续加载
        console.error('[index] Failed to fetch user:', e)
        return
      }
    }

    // 加载发薪日配置
    const list = await listPayday()
    const active = (list || []).filter(c => c.is_active === 1)
    hasPaydayConfig.value = active.length > 0
    if (active.length === 0) {
      daysToPayday.value = null
      return
    }
    const solar = active.filter(c => c.calendar_type === 'solar')
    const daysList = solar.length ? solar.map(c => daysToNextPayday(c.payday)) : [999]
    daysToPayday.value = Math.min(...daysList)
  } catch (error) {
    console.error('[index] loadPaydayData error:', error)
    hasPaydayConfig.value = false
    daysToPayday.value = null
  } finally {
    loading.value = false
  }
}

/**
 * 加载积分商品列表（首页推荐，显示前3个）
 */
async function loadPointProducts() {
  try {
    productsLoading.value = true
    const res = await getPointProducts()
    // 只取前3个商品作为推荐
    products.value = (res.products || []).slice(0, 3)
  } catch (error) {
    console.error('[index] loadPointProducts error:', error)
    // 静默失败，不影响用户体验
  } finally {
    productsLoading.value = false
  }
}

/**
 * 加载用户剩余积分
 */
async function loadUserPoints() {
  try {
    const res = await getMyPoints()
    // 后端返回 snake_case 字段，需要兼容
    availablePoints.value = res.available_points ?? res.availablePoints ?? 0
  } catch (error) {
    console.error('[index] loadUserPoints error:', error)
    // 静默失败
  }
}

/**
 * 加载热门话题（取前5个）
 */
async function loadTopics() {
  try {
    topicsLoading.value = true
    const allTopics = await getActiveTopics()
    // 按帖子数量降序排序，取前5个
    topics.value = allTopics.sort((a, b) => b.post_count - a.post_count).slice(0, 5)
  } catch (error) {
    console.error('[index] loadTopics error:', error)
    // 静默失败
  } finally {
    topicsLoading.value = false
  }
}

/**
 * 恢复保存的心情
 */
function loadSavedMood() {
  try {
    const saved = uni.getStorageSync(MOOD_STORAGE_KEY) as MoodType | undefined
    if (saved && moodOptions.some(o => o.value === saved)) {
      selectedMood.value = saved
    }
  } catch (error) {
    // Failed to load saved mood
  }
}

// 首次加载
loadSavedMood()

// 检查是否已登录
if (isLoggedIn.value) {
  loadPaydayData()
} else {
  loading.value = false
}

function setMood(mood) {
  selectedMood.value = mood
  try {
    uni.setStorageSync(MOOD_STORAGE_KEY, mood)
  } catch (error) {
    // Failed to save mood
  }
}

// 检查登录状态，未登录则跳转登录页
function checkLogin() {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return false
  }
  return true
}

function goFeed() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/feed/index' })
}

function goPaydaySetting() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/payday-setting/index' })
}

function goSalaryRecord() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/salary-record/index' })
}

function goInsights() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/insights/index' })
}

function goMembership() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/membership/index' })
}

function goCheckIn() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/checkin/index' })
}

function goProfile() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/profile/index' })
}

function goPointMall() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/point-mall/index' })
}

function goSavingGoal() {
  if (!checkLogin()) return
  uni.navigateTo({ url: '/pages/savings-goals/index' })
}

function goExpenseRecord() {
  if (!checkLogin()) return
  // 支出记录功能：跳转到工资记录页面，用户可以选择记录后添加支出
  uni.navigateTo({ url: '/pages/salary-record/index' })
}

function goToProductDetail(productId: string) {
  if (!checkLogin()) return
  uni.navigateTo({ url: `/pages/point-mall/detail/index?id=${productId}` })
}

/**
 * 处理快捷入口点击
 */
function handleQuickEntry(action: string) {
  if (!checkLogin()) return

  switch (action) {
    case 'goSalaryRecord':
      goSalaryRecord()
      break
    case 'goSavingGoal':
      goSavingGoal()
      break
    case 'goExpenseRecord':
      goExpenseRecord()
      break
    case 'goPointMall':
      goPointMall()
      break
    default:
      console.warn('[index] Unknown quick entry action:', action)
  }
}

/**
 * 点击话题 - 跳转到话题详情页
 */
function goToTopic(topicId: string) {
  if (!checkLogin()) return
  uni.navigateTo({ url: `/pages/topic-detail/index?id=${topicId}` })
}

/**
 * 发帖（带话题）
 */
function createPostWithTopic(topicId: string, topicName: string) {
  if (!checkLogin()) return
  // 跳转到发帖页面，并传递话题ID
  uni.navigateTo({
    url: `/pages/post-create/index?topicId=${topicId}&topicName=${encodeURIComponent(topicName)}`,
  })
}
</script>

<template>
  <view class="root-container">
    <!-- 用户信息栏 (登录后显示) -->
    <view v-if="isLoggedIn" class="user-bar" @click="goProfile">
      <image class="user-avatar" :src="userAvatar" mode="aspectFill" />
      <view class="user-info">
        <text class="user-name">{{ userName }}</text>
        <text class="user-points">{{ availablePoints }} 积分</text>
      </view>
      <text class="user-arrow">›</text>
    </view>

    <view class="payday-card">
      <text class="payday-title">发薪状态</text>
      <text v-if="loading" class="payday-desc">加载中…</text>
      <template v-else-if="!hasPaydayConfig">
        <text class="payday-desc">未设置发薪日</text>
        <button class="btn-link" @click="goPaydaySetting">去设置</button>
      </template>
      <text v-else-if="daysToPayday === 0" class="payday-desc">今天发薪日 🎉</text>
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

    <!-- 快捷入口 -->
    <view class="quick-entry-section">
      <view class="quick-entry-grid">
        <view
          v-for="entry in quickEntries"
          :key="entry.action"
          class="quick-entry-item"
          @click="handleQuickEntry(entry.action)"
        >
          <view class="quick-entry-icon">{{ entry.icon }}</view>
          <text class="quick-entry-label">{{ entry.label }}</text>
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

    <!-- 热门话题 -->
    <view class="topics-section">
      <view class="section-header">
        <text class="section-title">热门话题</text>
      </view>

      <view v-if="topicsLoading" class="topics-loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="topics.length > 0" class="topics-list">
        <view v-for="topic in topics" :key="topic.id" class="topic-item">
          <view class="topic-info" @click="goToTopic(topic.id)">
            <text class="topic-name"># {{ topic.name }}</text>
            <text class="topic-count">{{ topic.post_count }} 帖子</text>
          </view>
          <button class="topic-btn" @click="createPostWithTopic(topic.id, topic.name)">发帖</button>
        </view>
      </view>

      <view v-else class="topics-empty">
        <text>暂无话题</text>
      </view>
    </view>

    <!-- 积分商品推荐 -->
    <view v-if="isLoggedIn" class="products-section">
      <view class="section-header">
        <text class="section-title">积分兑换</text>
        <text class="more-link" @click="goPointMall">更多 ›</text>
      </view>

      <view v-if="productsLoading" class="products-loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="products.length > 0" class="products-list">
        <view
          v-for="product in products"
          :key="product.id"
          class="product-item"
          @click="goToProductDetail(product.id)"
        >
          <image
            v-if="product.image_url"
            class="product-image"
            :src="product.image_url"
            mode="aspectFill"
          />
          <view v-else class="product-image placeholder">
            <text>🎁</text>
          </view>
          <view class="product-info">
            <text class="product-name">{{ product.name }}</text>
            <view class="product-footer">
              <text class="product-points">{{ product.points_cost }} 积分</text>
              <text
                v-if="!product.stock_unlimited && product.stock <= 0"
                class="product-out-of-stock"
                >已售罄</text
              >
            </view>
          </view>
        </view>
      </view>

      <view v-else class="products-empty">
        <text>暂无可兑换商品</text>
      </view>
    </view>

    <!-- 底部安全区域 -->
    <view class="tabbar-placeholder" />

    <!-- 液态玻璃 TabBar -->
    <GlassTabBar />
  </view>
</template>

<style scoped lang="scss">
.root-container {
  padding: calc(5rpx + env(safe-area-inset-top)) 2.5rem;
  text-align: center;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #ffffff 100%);
}

/* 用户信息栏 */
.user-bar {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 1rem;
}

.user-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  margin-right: 16rpx;
  border: 2rpx solid rgba(74, 108, 247, 0.2);
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.user-name {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--text-primary);
  text-align: left;
}

.user-points {
  font-size: 24rpx;
  color: $brand-primary;
  font-weight: 600;
  text-align: left;
}

.user-arrow {
  font-size: 40rpx;
  color: var(--text-tertiary);
}

.payday-card {
  margin: 1rem 0;
  padding: 1.5rem 1rem;
  background: $gradient-brand;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(74, 108, 247, 0.25);
}

.payday-title {
  font-weight: 600;
  display: block;
  color: #fff;
  font-size: 28rpx;
}

.payday-desc {
  display: block;
  margin-top: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  font-size: 32rpx;
  font-weight: 600;
}

.entry-row {
  margin: 1rem 0;
}

.btn-primary {
  padding: 0.5rem 1.5rem;
  background: $gradient-brand;
  color: #fff;
  border: none;
  border-radius: 8px;
}

.btn-secondary {
  padding: 0.5rem 1.5rem;
  background: $brand-primary;
  color: #fff;
  border: none;
  border-radius: 8px;
  margin-left: 0.5rem;
}

.btn-outline {
  padding: 0.5rem 1.5rem;
  background: transparent;
  color: var(--brand-primary);
  border: 1px solid var(--brand-primary);
  border-radius: 8px;
}

.btn-link {
  margin-top: 0.5rem;
  padding: 0.25rem 0;
  background: none;
  border: none;
  color: #fff;
  font-size: 0.9rem;
  text-decoration: underline;
}

.mood-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  text-align: left;
}

.progress-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 16rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.06);
  text-align: left;
}

.section-title {
  font-weight: 600;
  font-size: 0.95rem;
  display: block;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.mood-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.mood-item {
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  border: 2rpx solid #e5e7eb;
  background: #f9fafb;
  color: var(--text-primary);
  transition: all 0.2s;
}

.mood-item.active {
  border-color: $brand-primary;
  background: rgba(74, 108, 247, 0.1);
  color: $brand-primary;
}

.mood-label {
  font-size: 0.9rem;
}

.progress-bar {
  height: 12rpx;
  background: #e5e7eb;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  background: $gradient-brand;
  border-radius: 6rpx;
  transition: width 0.2s;
}

.progress-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.5rem;
  display: block;
}

/* 积分商品区域 */
.products-section {
  margin: 2rem 0;
  text-align: left;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.more-link {
  font-size: 0.9rem;
  color: var(--brand-primary);
  cursor: pointer;
}

.products-loading,
.products-empty {
  text-align: center;
  padding: 2rem;
  background: #f8fafc;
  border-radius: 16rpx;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.products-list {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.product-item {
  flex-shrink: 0;
  width: 200rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.product-image {
  width: 200rpx;
  height: 200rpx;
  background: #f1f5f9;

  &.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 60rpx;
  }
}

.product-info {
  padding: 0.75rem;
  background: #fff;
}

.product-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-points {
  font-size: 0.9rem;
  font-weight: 600;
  color: $brand-primary;
}

.product-out-of-stock {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

/* 快捷入口区域 */
.quick-entry-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.quick-entry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.quick-entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.quick-entry-icon {
  width: 88rpx;
  height: 88rpx;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  transition: transform 0.2s, box-shadow 0.2s;
}

.quick-entry-item:active .quick-entry-icon {
  transform: scale(0.95);
}

.quick-entry-label {
  font-size: 24rpx;
  color: var(--text-secondary);
}

/* 热门话题区域 */
.topics-section {
  margin: 2rem 0;
  text-align: left;
}

.topics-loading,
.topics-empty {
  text-align: center;
  padding: 2rem;
  background: #f8fafc;
  border-radius: 16rpx;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.topic-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.topic-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  cursor: pointer;
}

.topic-name {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--text-primary);
}

.topic-count {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

.topic-btn {
  padding: 0.4rem 1rem;
  background: $gradient-brand;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  font-size: 24rpx;
  margin: 0;
}

.topic-btn::after {
  border: none;
}

/* TabBar 占位 */
.tabbar-placeholder {
  height: calc(120rpx + env(safe-area-inset-bottom));
}
</style>
