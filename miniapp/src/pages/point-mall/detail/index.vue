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
import { getPointProduct, createPointOrder, getMyAddresses } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'

const product = ref(null)
const loading = ref(false)
const availablePoints = ref(0)
const productId = ref('')
const selectedAddress = ref(null)

// 计算属性
const canExchange = computed(() => {
  if (!product.value) return false
  const hasStock = product.value.stock_unlimited || product.value.stock > 0
  const hasPoints = availablePoints.value >= product.value.points_cost
  const hasAddress = !needAddress.value || selectedAddress.value !== null
  return hasStock && hasPoints && hasAddress
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

onMounted(() => {
  // uni-app 的 onLoad 钩子需要通过页面参数获取
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const pageOptions = currentPage.options || {}
  productId.value = pageOptions.id || ''

  if (productId.value) {
    loadData()
  }
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
    const addresses = res.data?.items || []
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

// 地址选择回调（由地址列表页面调用）
window.onAddressSelected = (address) => {
  selectedAddress.value = address
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

<style scoped>
.product-detail-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.loading, .error {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 200rpx 0;
  color: #999;
}

.detail-content {
  padding-bottom: 120rpx;
}

.product-image-section {
  position: relative;
  background-color: #fff;
}

.product-image {
  width: 100%;
  height: 750rpx;
}

.product-image.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 120rpx;
}

.product-badges {
  position: absolute;
  top: 20rpx;
  left: 20rpx;
  display: flex;
  gap: 12rpx;
}

.badge {
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #fff;
}

.badge.virtual {
  background-color: #909399;
}

.badge.physical {
  background-color: #67c23a;
}

.badge.bundle {
  background-color: #e6a23c;
}

.badge.shipping {
  background-color: #409eff;
}

.product-info-section {
  padding: 30rpx;
  margin-top: 20rpx;
  background-color: #fff;
}

.product-name {
  font-size: 36rpx;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.product-desc {
  display: block;
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

.product-meta {
  display: flex;
  gap: 20rpx;
  margin-top: 20rpx;
}

.stock-info {
  padding: 8rpx 16rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  font-size: 24rpx;
}

.stock-available {
  color: #67c23a;
}

.stock-unlimited {
  color: #409eff;
}

.stock-empty {
  color: #f56c6c;
}

.category {
  padding: 8rpx 16rpx;
  background-color: #f0f0f0;
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #666;
}

.price-section {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 30rpx;
}

.price-label {
  font-size: 28rpx;
  color: #666;
}

.price-tag {
  display: flex;
  align-items: baseline;
  padding: 12rpx 24rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
}

.price-tag .points {
  font-size: 40rpx;
  font-weight: 500;
  color: #fff;
}

.price-tag .label {
  margin-left: 8rpx;
  font-size: 24rpx;
  color: #fff;
}

.my-balance {
  margin-left: auto;
  font-size: 24rpx;
  color: #999;
}

/* 地址区域 */
.address-section {
  margin-top: 20rpx;
  padding: 30rpx;
  background-color: #fff;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
}

.section-action {
  font-size: 26rpx;
  color: #667eea;
}

.selected-address {
  display: flex;
  justify-content: space-between;
  padding: 24rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
  border: 2rpx solid #667eea;
}

.address-content {
  flex: 1;
}

.address-top {
  display: flex;
  gap: 20rpx;
  margin-bottom: 12rpx;
}

.contact-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.contact-phone {
  font-size: 26rpx;
  color: #666;
}

.address-detail {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
}

.default-badge {
  padding: 8rpx 16rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8rpx;
  font-size: 20rpx;
  color: #fff;
}

.no-address {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
  border: 2rpx dashed #ddd;
  border-radius: 12rpx;
  background-color: #f8f9fa;
}

.no-address .icon {
  font-size: 60rpx;
  margin-bottom: 16rpx;
}

.no-address .text {
  font-size: 26rpx;
  color: #999;
}

.action-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 30rpx;
  background-color: #fff;
  border-top: 1rpx solid #eee;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.exchange-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  line-height: 88rpx;
  text-align: center;
}

.exchange-btn.disabled {
  opacity: 0.5;
}
</style>
