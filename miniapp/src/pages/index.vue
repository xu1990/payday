<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow, onLaunch } from '@dcloudio/uni-app'
import AppFooter from '@/components/AppFooter.vue'
import AppLogos from '@/components/AppLogos.vue'
import InputEntry from '@/components/InputEntry.vue'
import { listPayday } from '@/api/payday'
import { getPointProducts } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'
import type { MoodType } from '@/api/salary'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { handleQRCodeLaunch } from '@/utils/qrcode'

const MOOD_STORAGE_KEY = 'payday_home_mood'
const moodOptions: { value: MoodType; label: string }[] = [
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
const daysToPayday = ref<number | null>(null)
const hasPaydayConfig = ref(false)
const selectedMood = ref<MoodType>('happy')
const progress = ref(monthProgress())

// 积分商品相关
const products = ref<any[]>([])
const productsLoading = ref(false)

// 用户剩余积分
const availablePoints = ref(0)

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
    availablePoints.value = res.availablePoints || 0
  } catch (error) {
    console.error('[index] loadUserPoints error:', error)
    // 静默失败
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

function setMood(mood: MoodType) {
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

function goToProductDetail(productId: string) {
  if (!checkLogin()) return
  uni.navigateTo({ url: `/pages/point-mall/detail/index?id=${productId}` })
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

    <view class="progress-section">
      <text class="section-title">本月进度</text>
      <view class="progress-bar">
        <view class="progress-inner" :style="{ width: progress.ratio + '%' }" />
      </view>
      <text class="progress-desc">{{ progress.passed }} / {{ progress.total }} 天</text>
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
              <text v-if="!product.stock_unlimited && product.stock <= 0" class="product-out-of-stock">已售罄</text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="products-empty">
        <text>暂无可兑换商品</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.root-container {
  padding: calc(5rpx + env(safe-area-inset-top)) 2.5rem;
  text-align: center;
  min-height: 100vh;
}

/* 用户信息栏 */
.user-bar {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: #fff;
  border-radius: 12rpx;
  margin-bottom: 1rem;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.user-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  margin-right: 16rpx;
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
  color: #333;
  text-align: left;
}

.user-points {
  font-size: 24rpx;
  color: #ff6b6b;
  font-weight: 600;
  text-align: left;
}

.user-arrow {
  font-size: 40rpx;
  color: #999;
}

.payday-card {
  margin: 1rem 0;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 8px;
}

.payday-title {
  font-weight: 600;
  display: block;
}

.payday-desc {
  display: block;
  margin-top: 0.5rem;
  color: #666;
}

.entry-row {
  margin: 1rem 0;
}

.btn-primary {
  padding: 0.5rem 1.5rem;
  background: #07c160;
  color: #fff;
  border: none;
  border-radius: 8px;
}

.btn-secondary {
  padding: 0.5rem 1.5rem;
  background: #576b95;
  color: #fff;
  border: none;
  border-radius: 8px;
  margin-left: 0.5rem;
}

.btn-outline {
  padding: 0.5rem 1.5rem;
  background: transparent;
  color: #07c160;
  border: 1px solid #07c160;
  border-radius: 8px;
}

.btn-link {
  margin-top: 0.5rem;
  padding: 0.25rem 0;
  background: none;
  border: none;
  color: #07c160;
  font-size: 0.9rem;
}

.mood-section,
.progress-section {
  margin: 1rem 0;
  text-align: left;
}

.section-title {
  font-weight: 600;
  font-size: 0.95rem;
  display: block;
  margin-bottom: 0.5rem;
}

.mood-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.mood-item {
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  border: 1px solid #ddd;
  background: #fff;
}

.mood-item.active {
  border-color: #07c160;
  background: #e8f8f0;
}

.mood-label {
  font-size: 0.9rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  background: #07c160;
  border-radius: 4px;
  transition: width 0.2s;
}

.progress-desc {
  font-size: 0.85rem;
  color: #666;
  margin-top: 0.25rem;
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
  color: #07c160;
  cursor: pointer;
}

.products-loading,
.products-empty {
  text-align: center;
  padding: 2rem;
  color: #999;
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
  border-radius: 12rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
}

.product-image {
  width: 200rpx;
  height: 200rpx;
  background: #f5f5f5;

  &.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 60rpx;
  }
}

.product-info {
  padding: 0.75rem;
}

.product-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
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
  color: #ff6b6b;
}

.product-out-of-stock {
  font-size: 0.75rem;
  color: #999;
}
</style>
