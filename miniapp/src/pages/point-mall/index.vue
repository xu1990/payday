<template>
  <view class="point-mall-page">
    <!-- 积分余额显示 -->
    <view class="balance-bar">
      <view class="balance-info">
        <text class="label">可用积分</text>
        <text class="balance">{{ availablePoints || 0 }}</text>
      </view>
      <view class="order-btn" @tap="goToOrders">
        <text class="order-icon">📦</text>
        <text class="order-text">我的订单</text>
      </view>
    </view>

    <!-- 分类筛选 -->
    <view class="category-filter">
      <scroll-view scroll-x class="category-scroll">
        <view
          class="category-item"
          :class="{ active: !selectedCategory }"
          @tap="selectCategory('')"
        >
          <text>全部</text>
        </view>
        <view
          v-for="category in categories"
          :key="category"
          class="category-item"
          :class="{ active: selectedCategory === category }"
          @tap="selectCategory(category)"
        >
          <text>{{ category }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- 商品列表 -->
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="products.length === 0" class="empty">
      <text>暂无商品</text>
    </view>

    <view v-else class="products-list">
      <view
        v-for="product in products"
        :key="product.id"
        class="product-item"
        @tap="goToDetail(product)"
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
          <text v-if="product.description" class="product-desc">
            {{ product.description }}
          </text>

          <view class="product-footer">
            <view class="stock-info">
              <text v-if="product.stock_unlimited" class="stock-unlimited">库存无限</text>
              <text v-else-if="product.stock > 0" class="stock-available"
                >剩余{{ product.stock }}件</text
              >
              <text v-else class="stock-empty">已售罄</text>
            </view>
            <view class="price-tag">
              <text class="points">{{ getPriceDisplay(product).main }}</text>
              <text class="label">{{ getPriceDisplay(product).unit }}</text>
              <text v-if="getPriceDisplay(product).showPlus" class="plus-cash">
                + ¥{{ (getPriceDisplay(product).cashAmount / 100).toFixed(2) }}
              </text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPointProducts } from '@/api/pointShop'
import { getMyPoints } from '@/api/ability-points'

const products = ref([])
const loading = ref(false)
const selectedCategory = ref('')
const categories = ref([])
const availablePoints = ref(0)

onMounted(() => {
  loadPoints()
  loadProducts()
})

async function loadPoints() {
  try {
    const res = await getMyPoints()
    availablePoints.value = res.availablePoints || 0
  } catch (err) {
    console.error('Failed to load points:', err)
  }
}

async function loadProducts(category = '') {
  try {
    loading.value = true
    const res = await getPointProducts(category || undefined)
    products.value = res.products || []

    // 只有在加载全部商品时才更新分类列表
    if (!category) {
      const cats = new Set()
      products.value.forEach(p => {
        if (p.category) cats.add(p.category)
      })
      categories.value = Array.from(cats)
    }
  } catch (err) {
    console.error('Failed to load products:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function selectCategory(category) {
  selectedCategory.value = category
  loadProducts(category)
}

function goToDetail(product) {
  uni.navigateTo({
    url: `/pages/point-mall/detail/index?id=${product.id}`,
  })
}

function goToOrders() {
  uni.navigateTo({
    url: '/pages/point-mall/orders/index',
  })
}

/**
 * 根据支付模式获取价格显示文本
 */
function getPriceDisplay(product) {
  const mode = product.payment_mode || 'points_only'

  if (mode === 'points_only') {
    return {
      main: product.points_cost,
      unit: '积分',
      showPlus: false,
      cashAmount: 0,
    }
  } else if (mode === 'cash_only') {
    const cash = product.cash_price || 0
    return {
      main: (cash / 100).toFixed(2),
      unit: '元',
      showPlus: false,
      cashAmount: cash,
    }
  } else if (mode === 'mixed') {
    const points = product.mixed_points_cost || 0
    const cash = product.mixed_cash_price || 0
    return {
      main: points,
      unit: '积分',
      showPlus: true,
      cashAmount: cash,
    }
  }

  return {
    main: product.points_cost,
    unit: '积分',
    showPlus: false,
    cashAmount: 0,
  }
}
</script>

<style lang="scss" scoped>
.point-mall-page {
  min-height: 100vh;
  background: var(--bg-base);
}

.balance-bar {
  background: $gradient-brand;
  padding: $spacing-lg $spacing-md;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;

  .balance-info {
    flex: 1;
  }

  .label {
    font-size: $font-size-xs;
    opacity: 0.9;
  }

  .balance {
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
  }

  .order-btn {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    background: var(--bg-glass-subtle);
    padding: $spacing-sm $spacing-md;
    border-radius: $radius-full;
    backdrop-filter: blur(10rpx);

    .order-icon {
      font-size: $font-size-sm;
    }

    .order-text {
      font-size: $font-size-xs;
      font-weight: $font-weight-medium;
    }
  }
}

.category-filter {
  background: var(--bg-glass-standard);
  padding: $spacing-md 0;
  margin-bottom: $spacing-md;

  .category-scroll {
    white-space: nowrap;
    padding: 0 $spacing-md;

    .category-item {
      display: inline-block;
      padding: $spacing-xs $spacing-lg;
      margin-right: $spacing-sm;
      border-radius: $radius-full;
      font-size: $font-size-xs;
      background: var(--bg-base);
      color: var(--text-secondary);

      &.active {
        background: $gradient-brand;
        color: white;
      }
    }
  }
}

.loading,
.empty {
  text-align: center;
  padding: $spacing-2xl 0;
  color: var(--text-tertiary);
}

.products-list {
  padding: $spacing-md;

  .product-item {
    display: flex;
    @include glass-card();
    border-radius: $radius-lg;
    overflow: hidden;
    margin-bottom: $spacing-md;

    .product-image {
      width: 200rpx;
      height: 200rpx;
      flex-shrink: 0;

      &.placeholder {
        background: var(--bg-base);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60rpx;
      }
    }

    .product-info {
      flex: 1;
      padding: $spacing-md;
      display: flex;
      flex-direction: column;

      .product-name {
        font-size: $font-size-sm;
        font-weight: $font-weight-bold;
        margin-bottom: $spacing-xs;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
      }

      .product-desc {
        font-size: $font-size-xs;
        color: var(--text-tertiary);
        margin-bottom: auto;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
      }

      .product-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: $spacing-sm;

        .stock-info {
          font-size: $font-size-xs;

          .stock-unlimited {
            color: $brand-primary;
          }

          .stock-available {
            color: $semantic-success;
          }

          .stock-empty {
            color: $semantic-error;
          }
        }

        .price-tag {
          background: $gradient-brand;
          color: white;
          padding: $spacing-xs $spacing-md;
          border-radius: $radius-full;
          display: flex;
          align-items: center;

          .points {
            font-size: $font-size-sm;
            font-weight: $font-weight-bold;
            margin-right: $spacing-xs;
          }

          .label {
            font-size: $font-size-xs;
            opacity: 0.9;
          }

          .plus-cash {
            font-size: $font-size-xs;
            margin-left: $spacing-xs;
            opacity: 0.9;
          }
        }
      }
    }
  }
}
</style>
