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
      </view>

      <!-- 商品信息 -->
      <view class="product-info-section">
        <text class="product-name">{{ product.name }}</text>
        <text class="product-desc" v-if="product.description">
          {{ product.description }}
        </text>

        <view class="product-meta">
          <view class="stock-info">
            <text v-if="product.stock_unlimited" class="stock-unlimited">库存无限</text>
            <text v-else-if="product.stock > 0" class="stock-available">剩余{{ product.stock }}件</text>
            <text v-else class="stock-empty">已售罄</text>
          </view>
          <view class="category" v-if="product.category">
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
import { getPointProduct, createPointOrder } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'

const product = ref(null)
const loading = ref(false)
const availablePoints = ref(0)
const productId = ref('')

const canExchange = computed(() => {
  if (!product.value) return false
  const hasStock = product.value.stock_unlimited || product.value.stock > 0
  const hasPoints = availablePoints.value >= product.value.points_cost
  return hasStock && hasPoints
})

const exchangeButtonText = computed(() => {
  if (!product.value) return '加载中...'
  if (product.value.stock === 0 && !product.value.stock_unlimited) return '已售罄'
  if (availablePoints.value < product.value.points_cost) return '积分不足'
  return '立即兑换'
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
      getMyPoints()
    ])

    product.value = productRes
    availablePoints.value = pointsRes.availablePoints || 0
  } catch (err) {
    console.error('Failed to load data:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

async function handleExchange() {
  if (!canExchange.value) return

  try {
    const result = await uni.showModal({
      title: '确认兑换',
      content: `确定要消耗${product.value.points_cost}积分兑换"${product.value.name}"吗？`,
    })

    if (!result.confirm) return

    uni.showLoading({ title: '兑换中...' })

    await createPointOrder({
      product_id: productId.value
    })

    uni.hideLoading()

    uni.showToast({
      title: '兑换成功',
      icon: 'success'
    })

    // 延迟跳转到订单列表
    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/point-mall/orders'
      })
    }, 1500)
  } catch (err) {
    uni.hideLoading()
    console.error('Exchange failed:', err)
    uni.showToast({
      title: err.message || '兑换失败',
      icon: 'none'
    })
  }
}
</script>

<style lang="scss" scoped>
.product-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.loading,
.error {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.detail-content {
  .product-image-section {
    background: white;
    padding: 20rpx;

    .product-image {
      width: 100%;
      height: 500rpx;
      border-radius: 20rpx;

      &.placeholder {
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 120rpx;
      }
    }
  }

  .product-info-section {
    background: white;
    margin-top: 20rpx;
    padding: 30rpx;

    .product-name {
      display: block;
      font-size: 32rpx;
      font-weight: bold;
      margin-bottom: 20rpx;
    }

    .product-desc {
      display: block;
      font-size: 26rpx;
      color: #666;
      line-height: 1.6;
      margin-bottom: 30rpx;
    }

    .product-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30rpx;

      .stock-info {
        font-size: 24rpx;

        .stock-unlimited {
          color: #1890ff;
        }

        .stock-available {
          color: #52c41a;
        }

        .stock-empty {
          color: #ff4d4f;
        }
      }

      .category {
        background: #f0f0f0;
        color: #666;
        padding: 5rpx 15rpx;
        border-radius: 15rpx;
        font-size: 22rpx;
      }
    }

    .price-section {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
      border-radius: 20rpx;
      padding: 25rpx;
      display: flex;
      align-items: center;
      justify-content: space-between;

      .price-label {
        font-size: 26rpx;
        color: #666;
      }

      .price-tag {
        .points {
          font-size: 40rpx;
          font-weight: bold;
          color: #667eea;
          margin-right: 5rpx;
        }

        .label {
          font-size: 24rpx;
          color: #667eea;
        }
      }

      .my-balance {
        font-size: 24rpx;
        color: #999;
      }
    }
  }

  .action-section {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 20rpx;
    background: white;
    box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.1);

    .exchange-btn {
      width: 100%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 50rpx;
      padding: 25rpx;
      font-size: 30rpx;
      font-weight: bold;

      &.disabled {
        background: #ccc;
      }

      &::after {
        border: none;
      }
    }
  }
}
</style>
