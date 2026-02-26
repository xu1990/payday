<template>
  <view class="product-detail-page">
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="!product" class="error">
      <text>商品不存在</text>
    </view>

    <view v-else class="detail-content">
      <!-- 商品图片 -->
      <view class="product-image-section">
        <image
          v-if="product.image_url"
          class="product-image"
          :src="product.image_url"
          mode="aspectFill"
        />
        <view v-else class="product-image placeholder">
          <text>🎁</text>
        </view>

        <!-- 商品类型标签 -->
        <view class="product-badges">
          <view v-if="product.product_type === 'virtual'" class="badge virtual">虚拟商品</view>
          <view v-else-if="product.product_type === 'bundle'" class="badge bundle">套餐商品</view>
          <view v-else class="badge physical">实物商品</view>

          <view v-if="shippingMethodText" class="badge shipping">{{ shippingMethodText }}</view>
        </view>
      </view>

      <!-- 商品信息 -->
      <view class="product-info-section">
        <text class="product-name">{{ product.name }}</text>
        <text v-if="product.description" class="product-desc">
          {{ product.description }}
        </text>

        <view class="product-meta">
          <view class="stock-info">
            <text v-if="product.stock_unlimited" class="stock-unlimited">库存无限</text>
            <text v-else-if="product.stock > 0" class="stock-available"
              >剩余{{ product.stock }}件</text
            >
            <text v-else class="stock-empty">已售罄</text>
          </view>
          <view v-if="product.category" class="category">
            <text>{{ product.category }}</text>
          </view>
        </view>

        <view class="price-section">
          <text class="price-label">兑换所需</text>
          <view class="price-tag">
            <text class="points">{{ product.points_cost }}</text>
            <text class="label">积分</text>
          </view>
          <text class="my-balance">我的积分：{{ availablePoints }}</text>
        </view>
      </view>

      <!-- 收货地址（仅实物商品需要地址时） -->
      <view v-if="needAddress" class="address-section">
        <view class="section-header">
          <text class="section-title">收货地址</text>
          <text class="section-action" @tap="goToAddresses">
            {{ selectedAddress ? '更换' : '选择' }} ›
          </text>
        </view>

        <view v-if="selectedAddress" class="selected-address" @tap="goToAddresses">
          <view class="address-content">
            <view class="address-top">
              <text class="contact-name">{{ selectedAddress.contact_name }}</text>
              <text class="contact-phone">{{ selectedAddress.contact_phone }}</text>
            </view>
            <view class="address-detail">
              <text>{{ selectedAddress.province_name }}{{ selectedAddress.city_name }}{{ selectedAddress.district_name }}</text>
              <text>{{ selectedAddress.detailed_address }}</text>
            </view>
          </view>
          <view v-if="selectedAddress.is_default" class="default-badge">默认</view>
        </view>

        <view v-else class="no-address" @tap="goToAddresses">
          <text class="icon">📍</text>
          <text class="text">请选择收货地址</text>
        </view>

        <!-- 配送状态提示 -->
        <view v-if="selectedAddress && product.shipping_template && deliveryStatus" class="delivery-status" :class="{ 'can-deliver': deliveryStatus.canDeliver, 'cannot-deliver': !deliveryStatus.canDeliver }">
          <text class="status-icon">{{ deliveryStatus.canDeliver ? '✓' : '✗' }}</text>
          <text class="status-text">{{ deliveryStatus.message }}</text>
        </view>
      </view>

      <!-- 配送信息（有运费模板时显示） -->
      <view v-if="product.shipping_template" class="shipping-section">
        <view class="section-header">
          <text class="section-title">配送信息</text>
        </view>
        <view class="shipping-info">
          <!-- 预计到达时间 -->
          <view v-if="product.shipping_template.estimate_days_min" class="shipping-row">
            <text class="shipping-label">预计到达</text>
            <text class="shipping-value">
              {{ product.shipping_template.estimate_days_min }}-{{ product.shipping_template.estimate_days_max }}天
            </text>
          </view>
          <!-- 配送区域 -->
          <view v-if="product.shipping_template.delivery_region_names?.length" class="shipping-row">
            <text class="shipping-label">配送区域</text>
            <text class="shipping-value">{{ product.shipping_template.delivery_region_names.join('、') }}</text>
          </view>
          <!-- 不配送区域 -->
          <view v-if="product.shipping_template.excluded_region_names?.length" class="shipping-row excluded">
            <text class="shipping-label">不配送区域</text>
            <text class="shipping-value">{{ product.shipping_template.excluded_region_names.join('、') }}</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-section">
        <button
          class="exchange-btn"
          :class="{ disabled: !canExchange }"
          :disabled="!canExchange"
          @tap="handleExchange"
        >
          {{ exchangeButtonText }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getPointProduct, createPointOrder, getMyAddresses } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'

const product = ref(null)
const loading = ref(false)
const availablePoints = ref(0)
const productId = ref('')
const selectedAddress = ref(null)
const isInitialized = ref(false)

// 计算属性
const canExchange = computed(() => {
  if (!product.value) return false
  const hasStock = product.value.stock_unlimited || product.value.stock > 0
  const hasPoints = availablePoints.value >= product.value.points_cost
  const hasAddress = !needAddress.value || selectedAddress.value !== null
  const canDeliver = !deliveryStatus.value || deliveryStatus.value.canDeliver
  return hasStock && hasPoints && hasAddress && canDeliver
})

const needAddress = computed(() => {
  if (!product.value) return false
  // 实物商品且需要快递或自提时，需要地址
  return product.value.product_type === 'physical' &&
         product.value.shipping_method !== 'no_shipping'
})

const exchangeButtonText = computed(() => {
  if (!product.value) return '加载中...'
  if (product.value.stock === 0 && !product.value.stock_unlimited) return '已售罄'
  if (availablePoints.value < product.value.points_cost) return '积分不足'
  if (needAddress.value && !selectedAddress.value) return '请选择收货地址'
  if (deliveryStatus.value && !deliveryStatus.value.canDeliver) return '该地址不可配送'
  return '立即兑换'
})

const shippingMethodText = computed(() => {
  if (!product.value) return ''
  const methodMap = {
    express: '快递发货',
    self_pickup: '用户自提',
    no_shipping: '无需快递',
  }
  return methodMap[product.value.shipping_method] || ''
})

// 配送区域校验
const deliveryStatus = computed(() => {
  // 如果不需要地址或没有运费模板，默认可配送
  if (!needAddress.value || !product.value?.shipping_template) {
    return { canDeliver: true, message: '' }
  }

  // 如果没有选择地址，不校验
  if (!selectedAddress.value) {
    return { canDeliver: true, message: '' }
  }

  const template = product.value.shipping_template
  const province = selectedAddress.value.province_name

  // 检查是否在不配送区域
  if (template.excluded_region_names?.length) {
    const excluded = template.excluded_region_names.some(name =>
      name.includes(province) || province.includes(name)
    )
    if (excluded) {
      return { canDeliver: false, message: `该地址在不配送区域内（${province}）` }
    }
  }

  // 检查是否在配送区域（如果指定了配送区域）
  if (template.delivery_region_names?.length) {
    const inDelivery = template.delivery_region_names.some(name =>
      name.includes(province) || province.includes(name)
    )
    if (!inDelivery) {
      return { canDeliver: false, message: `该地址不在配送区域内（${province}）` }
    }
  }

  return { canDeliver: true, message: '该地址可配送' }
})

onMounted(() => {
  // uni-app 的 onLoad 钩子需要通过页面参数获取
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const pageOptions = currentPage.options || {}
  productId.value = pageOptions.id || ''

  if (productId.value) {
    loadData()
  }
  isInitialized.value = true
})

// 每次页面显示时刷新地址（从地址列表页返回时自动刷新）
onShow(() => {
  // 只在需要地址且没有选中地址时加载默认地址
  if (isInitialized.value && needAddress.value && !selectedAddress.value) {
    loadDefaultAddress()
  }
})

// 暴露给地址列表页回调的函数
function onAddressSelected(address) {
  selectedAddress.value = address
}

defineExpose({
  onAddressSelected,
})

async function loadData() {
  try {
    loading.value = true

    // 并行加载商品和积分
    const [productRes, pointsRes] = await Promise.all([
      getPointProduct(productId.value),
      getMyPoints(),
    ])

    product.value = productRes
    availablePoints.value = pointsRes.availablePoints || 0

    // 如果需要地址，加载默认地址
    if (needAddress.value) {
      await loadDefaultAddress()
    }
  } catch (err) {
    console.error('Failed to load data:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

async function loadDefaultAddress() {
  try {
    const res = await getMyAddresses(true)
    const addresses = res.items || []
    // 找到默认地址
    const defaultAddr = addresses.find(addr => addr.is_default)
    if (defaultAddr) {
      selectedAddress.value = defaultAddr
    }
  } catch (err) {
    console.error('Failed to load addresses:', err)
  }
}

function goToAddresses() {
  // 跳转到地址列表，传递select=true表示选择模式
  uni.navigateTo({
    url: '/pages/point-mall/addresses/index?select=true',
  })
}

async function handleExchange() {
  if (!canExchange.value || !product.value) return

  try {
    const result = await uni.showModal({
      title: '确认兑换',
      content: `确定要消耗${product.value.points_cost}积分兑换"${product.value.name}"吗？`,
    })

    if (!result.confirm) return

    uni.showLoading({ title: '兑换中...' })

    const orderData = {
      product_id: productId.value,
    }

    // 如果需要地址，添加地址ID
    if (needAddress.value && selectedAddress.value) {
      orderData.address_id = selectedAddress.value.id
    }

    await createPointOrder(orderData)

    uni.hideLoading()

    uni.showToast({
      title: '兑换成功',
      icon: 'success',
    })

    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/point-mall/orders/index',
      })
    }, 500)
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: '兑换失败',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.product-detail-page {
  min-height: 100vh;
  background: var(--bg-base);
}

.loading, .error {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: $spacing-2xl 0;
  color: var(--text-tertiary);
}

.detail-content {
  padding-bottom: 120rpx;
}

.product-image-section {
  position: relative;
  background: var(--bg-glass-standard);
}

.product-image {
  width: 100%;
  height: 750rpx;
}

.product-image.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  background: $gradient-brand;
  color: #fff;
  font-size: 120rpx;
}

.product-badges {
  position: absolute;
  top: $spacing-md;
  left: $spacing-md;
  display: flex;
  gap: $spacing-sm;
}

.badge {
  padding: $spacing-xs $spacing-sm;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: #fff;
}

.badge.virtual {
  background-color: var(--text-tertiary);
}

.badge.physical {
  background-color: $semantic-success;
}

.badge.bundle {
  background-color: $semantic-warning;
}

.badge.shipping {
  background-color: $brand-primary;
}

.product-info-section {
  padding: $spacing-lg;
  margin-top: $spacing-md;
  @include glass-card();
}

.product-name {
  font-size: $font-size-xl;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
  line-height: 1.4;
}

.product-desc {
  display: block;
  margin-top: $spacing-md;
  font-size: $font-size-sm;
  color: var(--text-secondary);
  line-height: 1.6;
}

.product-meta {
  display: flex;
  gap: $spacing-md;
  margin-top: $spacing-md;
}

.stock-info {
  padding: $spacing-xs $spacing-sm;
  background: var(--bg-base);
  border-radius: $radius-sm;
  font-size: $font-size-xs;
}

.stock-available {
  color: $semantic-success;
}

.stock-unlimited {
  color: $brand-primary;
}

.stock-empty {
  color: $semantic-error;
}

.category {
  padding: $spacing-xs $spacing-sm;
  background: var(--bg-base);
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: var(--text-secondary);
}

.price-section {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-top: $spacing-lg;
}

.price-label {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.price-tag {
  display: flex;
  align-items: baseline;
  padding: $spacing-sm $spacing-lg;
  background: $gradient-brand;
  border-radius: $radius-full;
}

.price-tag .points {
  font-size: $font-size-2xl;
  font-weight: $font-weight-medium;
  color: #fff;
}

.price-tag .label {
  margin-left: $spacing-xs;
  font-size: $font-size-xs;
  color: #fff;
}

.my-balance {
  margin-left: auto;
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

/* 地址区域 */
.address-section {
  margin-top: $spacing-md;
  padding: $spacing-lg;
  @include glass-card();
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
}

.section-action {
  font-size: $font-size-xs;
  color: $brand-primary;
}

.selected-address {
  display: flex;
  justify-content: space-between;
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
  border: 2rpx solid $brand-primary;
}

.address-content {
  flex: 1;
}

.address-top {
  display: flex;
  gap: $spacing-md;
  margin-bottom: $spacing-sm;
}

.contact-name {
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
}

.contact-phone {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.address-detail {
  font-size: $font-size-sm;
  color: var(--text-secondary);
  line-height: 1.6;
}

.default-badge {
  padding: $spacing-xs $spacing-sm;
  background: $gradient-brand;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: #fff;
}

.no-address {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
  border: 2rpx dashed var(--border-regular);
  border-radius: $radius-md;
  background: var(--bg-glass-subtle);
}

.no-address .icon {
  font-size: 60rpx;
  margin-bottom: $spacing-md;
}

.no-address .text {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

/* 配送状态提示 */
.delivery-status {
  display: flex;
  align-items: center;
  padding: $spacing-md;
  margin-top: $spacing-sm;
  border-radius: $radius-md;
  font-size: $font-size-sm;
}

.delivery-status.can-deliver {
  background-color: rgba($semantic-success, 0.1);
  border: 2rpx solid $semantic-success;
}

.delivery-status.cannot-deliver {
  background-color: rgba($semantic-error, 0.1);
  border: 2rpx solid $semantic-error;
}

.delivery-status .status-icon {
  margin-right: $spacing-sm;
  font-size: $font-size-lg;
}

.delivery-status.can-deliver .status-icon {
  color: $semantic-success;
}

.delivery-status.cannot-deliver .status-icon {
  color: $semantic-error;
}

.delivery-status .status-text {
  flex: 1;
}

.delivery-status.can-deliver .status-text {
  color: darken($semantic-success, 20%);
}

.delivery-status.cannot-deliver .status-text {
  color: darken($semantic-error, 20%);
}

/* 配送信息区域 */
.shipping-section {
  margin-top: $spacing-md;
  padding: $spacing-lg;
  @include glass-card();
}

.shipping-info {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.shipping-row {
  display: flex;
  align-items: flex-start;
}

.shipping-label {
  width: 160rpx;
  flex-shrink: 0;
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

.shipping-value {
  flex: 1;
  font-size: $font-size-sm;
  color: var(--text-primary);
  line-height: 1.5;
}

.shipping-row.excluded .shipping-value {
  color: $semantic-error;
}

.action-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: $spacing-md $spacing-lg;
  background: var(--bg-glass-standard);
  border-top: 1rpx solid var(--border-subtle);
  box-shadow: $shadow-sm;
}

.exchange-btn {
  width: 100%;
  height: 88rpx;
  background: $gradient-brand;
  border-radius: $radius-full;
  color: #fff;
  font-size: $font-size-base;
  line-height: 88rpx;
  text-align: center;
}

.exchange-btn.disabled {
  opacity: 0.5;
}
</style>
