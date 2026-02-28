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
          v-if="displayImageUrl"
          class="product-image"
          :src="displayImageUrl"
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
            <text v-if="displayStockUnlimited" class="stock-unlimited">库存无限</text>
            <text v-else-if="displayStock > 0" class="stock-available"
              >剩余{{ displayStock }}件</text
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
            <text class="points">{{ displayPointsCost }}</text>
            <text class="label">积分</text>
          </view>
          <text class="my-balance">我的积分：{{ availablePoints }}</text>
        </view>
      </view>

      <!-- SKU选择区域（仅SKU商品显示） -->
      <view v-if="product.has_sku && product.specifications" class="sku-section">
        <view class="section-header">
          <text class="section-title">规格选择</text>
          <text v-if="selectedSku" class="section-hint">已选：{{ selectedSkuSpecsText }}</text>
        </view>

        <!-- 规格选择 -->
        <view v-for="(spec, specIndex) in product.specifications" :key="spec.id" class="spec-group" :class="`spec-group-${specIndex % 3}`">
          <view class="spec-label">
            <text class="spec-name">{{ spec.name }}</text>
            <text class="spec-required">*</text>
          </view>
          <view class="spec-values">
            <view
              v-for="value in spec.values"
              :key="value.id"
              class="spec-value"
              :class="{
                active: selectedSpecs[spec.name] === value.value,
                disabled: !isSpecValueAvailable(spec.name, value.value),
                'has-image': value.image_url
              }"
              @tap="selectSpec(spec.name, value.value)"
            >
              <image
                v-if="value.image_url"
                class="spec-value-image"
                :src="value.image_url"
                mode="aspectFill"
              />
              <text class="spec-value-text">{{ value.value }}</text>
              <view v-if="selectedSpecs[spec.name] === value.value" class="spec-check-icon">✓</view>
            </view>
          </view>
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

      <!-- 配送信息（实物商品且有运费模板时显示） -->
      <view v-if="product.shipping_template && needAddress" class="shipping-section">
        <view class="section-header">
          <text class="section-title">配送信息</text>
        </view>
        <view class="shipping-info">
          <!-- 运费显示 -->
          <view v-if="selectedAddress" class="shipping-row shipping-cost-row">
            <text class="shipping-label">运费</text>
            <view v-if="shippingCostLoading" class="shipping-value loading-text">计算中...</view>
            <view v-else-if="shippingCostInfo" class="shipping-value shipping-cost-value">
              <text v-if="shippingCostInfo.free_shipping" class="free-shipping">免运费</text>
              <text v-else class="cost">¥{{ (shippingCostInfo.shipping_cost / 100).toFixed(2) }}</text>
              <text v-if="shippingCostInfo.free_shipping && shippingCostInfo.free_shipping_reason" class="free-reason">
                （{{ shippingCostInfo.free_shipping_reason === 'seller' ? '商家承担' :
                    shippingCostInfo.free_shipping_reason === 'quantity' ? '满件包邮' :
                    shippingCostInfo.free_shipping_reason === 'amount' ? '满额包邮' : '' }}）
              </text>
            </view>
            <view v-else class="shipping-value">-</view>
          </view>
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
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getPointProduct, createPointOrder, getMyAddresses, calculateShippingCost } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'

const product = ref(null)
const loading = ref(false)
const availablePoints = ref(0)
const productId = ref('')
const selectedAddress = ref(null)
const isInitialized = ref(false)

// 运费状态
const shippingCostInfo = ref(null)
const shippingCostLoading = ref(false)

// SKU相关状态
const selectedSpecs = reactive({}) // { "颜色": "红色", "尺寸": "L" }
const selectedSku = ref(null)

// 计算属性 - 显示的图片URL（优先使用选中的SKU图片）
const displayImageUrl = computed(() => {
  if (selectedSku.value?.image_url) {
    return selectedSku.value.image_url
  }
  return product.value?.image_url
})

// 计算属性 - 显示的库存（根据选中的SKU或商品本身）
const displayStock = computed(() => {
  if (product.value?.has_sku && selectedSku.value) {
    return selectedSku.value.stock_unlimited ? 999 : selectedSku.value.stock
  }
  return product.value?.stock_unlimited ? 999 : (product.value?.stock || 0)
})

// 计算属性 - 显示的库存是否无限
const displayStockUnlimited = computed(() => {
  if (product.value?.has_sku && selectedSku.value) {
    return selectedSku.value.stock_unlimited
  }
  return product.value?.stock_unlimited
})

// 计算属性 - 显示的积分价格（根据选中的SKU或商品本身）
const displayPointsCost = computed(() => {
  if (product.value?.has_sku && selectedSku.value) {
    return selectedSku.value.points_cost
  }
  return product.value?.points_cost || 0
})

// 计算属性 - 选中SKU的规格文本
const selectedSkuSpecsText = computed(() => {
  if (!selectedSku.value) return ''
  const specs = selectedSku.value.specs
  if (typeof specs === 'string') {
    try {
      const parsed = JSON.parse(specs)
      return Object.entries(parsed).map(([k, v]) => `${k}:${v}`).join(' ')
    } catch {
      return ''
    }
  }
  if (typeof specs === 'object') {
    return Object.entries(specs).map(([k, v]) => `${k}:${v}`).join(' ')
  }
  return ''
})

// 检查规格值是否可用（是否有对应的SKU且有库存）
function isSpecValueAvailable(specName, specValue) {
  if (!product.value?.skus) return true

  // 构建临时规格选择，用于检查
  const tempSpecs = { ...selectedSpecs, [specName]: specValue }

  // 查找是否有匹配此规格组合的SKU
  const matchingSku = product.value.skus.find(sku => {
    const skuSpecs = typeof sku.specs === 'string' ? JSON.parse(sku.specs) : sku.specs
    // 检查所有规格是否匹配
    for (const [key, value] of Object.entries(tempSpecs)) {
      if (skuSpecs[key] !== value) {
        return false
      }
    }
    // 如果还有未选择的规格，只检查已选择的部分
    for (const [key, value] of Object.entries(skuSpecs)) {
      if (tempSpecs[key] !== undefined && tempSpecs[key] !== value) {
        return false
      }
    }
    return true
  })

  // 如果找到匹配的SKU，检查是否有库存
  if (matchingSku) {
    return matchingSku.stock_unlimited || matchingSku.stock > 0
  }

  // 如果没有找到匹配的SKU，可能是规格组合不存在
  return true // 允许选择，让用户看到最终结果
}

// 选择规格
function selectSpec(specName, specValue) {
  selectedSpecs[specName] = specValue
  updateSelectedSku()
}

// 更新选中的SKU
function updateSelectedSku() {
  if (!product.value?.has_sku || !product.value?.skus) {
    selectedSku.value = null
    return
  }

  // 检查是否所有规格都已选择
  const specNames = product.value.specifications?.map(s => s.name) || []
  const allSpecsSelected = specNames.every(name => selectedSpecs[name])

  if (!allSpecsSelected) {
    selectedSku.value = null
    return
  }

  // 查找匹配的SKU
  const matchingSku = product.value.skus.find(sku => {
    const skuSpecs = typeof sku.specs === 'string' ? JSON.parse(sku.specs) : sku.specs
    for (const [key, value] of Object.entries(selectedSpecs)) {
      if (skuSpecs[key] !== value) {
        return false
      }
    }
    return true
  })

  selectedSku.value = matchingSku || null
}

// 计算属性
const canExchange = computed(() => {
  if (!product.value) return false

  // SKU商品必须选择完整的规格
  if (product.value.has_sku && !selectedSku.value) return false

  // SKU商品检查SKU库存
  let hasStock = false
  if (product.value.has_sku && selectedSku.value) {
    hasStock = selectedSku.value.stock_unlimited || selectedSku.value.stock > 0
  } else {
    hasStock = product.value.stock_unlimited || product.value.stock > 0
  }

  const displayCost = product.value.has_sku && selectedSku.value
    ? selectedSku.value.points_cost
    : product.value.points_cost
  const hasPoints = availablePoints.value >= displayCost
  const hasAddress = !needAddress.value || selectedAddress.value !== null
  const canDeliver = !deliveryStatus.value || deliveryStatus.value.canDeliver
  return hasStock && hasPoints && hasAddress && canDeliver
})

const needAddress = computed(() => {
  if (!product.value) return false
  // 只有虚拟商品不需要地址
  // 实物和套餐商品需要快递或自提时，需要地址
  return product.value.product_type !== 'virtual' &&
         product.value.shipping_method !== 'no_shipping'
})

const exchangeButtonText = computed(() => {
  if (!product.value) return '加载中...'

  // SKU商品必须选择完整规格
  if (product.value.has_sku && !selectedSku.value) {
    return '请选择规格'
  }

  // 检查库存
  let stockEmpty = false
  if (product.value.has_sku && selectedSku.value) {
    stockEmpty = !selectedSku.value.stock_unlimited && selectedSku.value.stock <= 0
  } else {
    stockEmpty = !product.value.stock_unlimited && product.value.stock <= 0
  }
  if (stockEmpty) return '已售罄'

  // 检查积分
  const displayCost = product.value.has_sku && selectedSku.value
    ? selectedSku.value.points_cost
    : product.value.points_cost
  if (availablePoints.value < displayCost) return '积分不足'

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
    // 后端返回 snake_case 字段，需要兼容
    availablePoints.value = pointsRes.available_points ?? pointsRes.availablePoints ?? 0

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
      // 加载运费信息
      loadShippingCost()
    }
  } catch (err) {
    console.error('Failed to load addresses:', err)
  }
}

// 计算运费
async function loadShippingCost() {
  if (!product.value || !selectedAddress.value) {
    shippingCostInfo.value = null
    return
  }

  // 虚拟商品或无需快递的商品不计算运费
  if (product.value.product_type === 'virtual' || product.value.shipping_method === 'no_shipping') {
    shippingCostInfo.value = {
      deliverable: true,
      shipping_cost: 0,
      free_shipping: true,
      free_shipping_reason: 'no_shipping_needed'
    }
    return
  }

  // 没有运费模板，不计算
  if (!product.value.shipping_template_id) {
    shippingCostInfo.value = {
      deliverable: true,
      shipping_cost: 0,
      free_shipping: true,
      free_shipping_reason: 'no_template'
    }
    return
  }

  try {
    shippingCostLoading.value = true
    const res = await calculateShippingCost({
      product_id: productId.value,
      address_id: selectedAddress.value.id,
      sku_id: selectedSku.value?.id,
      quantity: 1
    })
    shippingCostInfo.value = res
  } catch (err) {
    console.error('Failed to calculate shipping cost:', err)
    shippingCostInfo.value = null
  } finally {
    shippingCostLoading.value = false
  }
}

// 监听地址变化，重新计算运费
watch(selectedAddress, () => {
  if (selectedAddress.value && product.value) {
    loadShippingCost()
  } else {
    shippingCostInfo.value = null
  }
})

// 监听SKU变化，重新计算运费（如果SKU影响运费）
watch(selectedSku, () => {
  if (selectedAddress.value && product.value) {
    loadShippingCost()
  }
})

function goToAddresses() {
  // 跳转到地址列表，传递select=true表示选择模式
  uni.navigateTo({
    url: '/pages/point-mall/addresses/index?select=true',
  })
}

// 生成幂等性键（防止重复提交）
function generateIdempotencyKey() {
  // 使用时间戳 + 随机字符串生成唯一键
  const timestamp = Date.now().toString(36)
  const randomStr = Math.random().toString(36).substring(2, 11)
  return `order_${timestamp}_${randomStr}`
}

async function handleExchange() {
  if (!canExchange.value || !product.value) return

  const displayCost = product.value.has_sku && selectedSku.value
    ? selectedSku.value.points_cost
    : product.value.points_cost

  try {
    const result = await uni.showModal({
      title: '确认兑换',
      content: `确定要消耗${displayCost}积分兑换"${product.value.name}"吗？`,
    })

    if (!result.confirm) return

    uni.showLoading({ title: '兑换中...' })

    const orderData = {
      product_id: productId.value,
      idempotency_key: generateIdempotencyKey(), // 幂等性键，防止重复提交
    }

    // 如果需要地址，添加地址ID
    if (needAddress.value && selectedAddress.value) {
      orderData.address_id = selectedAddress.value.id
    }

    // 如果是SKU商品，添加SKU ID
    if (product.value.has_sku && selectedSku.value) {
      orderData.sku_id = selectedSku.value.id
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

/* SKU选择区域 */
.sku-section {
  margin-top: $spacing-md;
  padding: $spacing-lg;
  @include glass-card();
}

.section-hint {
  font-size: $font-size-xs;
  color: $brand-primary;
  background: rgba($brand-primary, 0.1);
  padding: $spacing-xs $spacing-sm;
  border-radius: $radius-sm;
}

.spec-group {
  margin-top: $spacing-lg;
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
  border-left: 6rpx solid $brand-primary;

  &:first-child {
    margin-top: 0;
  }

  // 不同规格组的颜色区分
  &.spec-group-0 {
    border-left-color: $brand-primary;
  }

  &.spec-group-1 {
    border-left-color: $semantic-success;
  }

  &.spec-group-2 {
    border-left-color: $semantic-warning;
  }
}

.spec-label {
  display: flex;
  align-items: center;
  margin-bottom: $spacing-md;
}

.spec-name {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
}

.spec-required {
  margin-left: $spacing-xs;
  font-size: $font-size-xs;
  color: $semantic-error;
}

.spec-values {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.spec-value {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  min-width: 120rpx;
  background: var(--bg-base);
  border: 2rpx solid var(--border-regular);
  border-radius: $radius-md;
  transition: all 0.25s ease;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);

  &.has-image {
    padding: $spacing-sm;
    min-width: 140rpx;
  }

  &.active {
    background: linear-gradient(135deg, rgba($brand-primary, 0.1), rgba($brand-primary, 0.05));
    border-color: $brand-primary;
    border-width: 3rpx;
    box-shadow: 0 4rpx 12rpx rgba($brand-primary, 0.2);
    transform: scale(1.02);
  }

  &.disabled {
    opacity: 0.35;
    background: var(--bg-base);
    border-style: dashed;

    .spec-value-text {
      text-decoration: line-through;
      color: var(--text-tertiary);
    }
  }
}

.spec-value-image {
  width: 80rpx;
  height: 80rpx;
  border-radius: $radius-sm;
  margin-bottom: $spacing-xs;
  border: 2rpx solid var(--border-subtle);
}

.spec-value-text {
  font-size: $font-size-sm;
  color: var(--text-primary);
  font-weight: $font-weight-medium;
  text-align: center;
}

.spec-check-icon {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  width: 36rpx;
  height: 36rpx;
  background: $brand-primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-xs;
  color: #fff;
  box-shadow: 0 2rpx 6rpx rgba($brand-primary, 0.4);
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

/* 运费样式 */
.shipping-cost-row {
  padding: $spacing-sm;
  background: var(--bg-glass-subtle);
  border-radius: $radius-sm;
  margin-bottom: $spacing-sm;
}

.shipping-cost-value {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: $spacing-xs;
}

.shipping-cost-value .free-shipping {
  color: $semantic-success;
  font-weight: $font-weight-bold;
}

.shipping-cost-value .cost {
  color: $semantic-error;
  font-weight: $font-weight-bold;
  font-size: $font-size-base;
}

.shipping-cost-value .free-reason {
  color: var(--text-tertiary);
  font-size: $font-size-xs;
}

.loading-text {
  color: var(--text-tertiary);
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
