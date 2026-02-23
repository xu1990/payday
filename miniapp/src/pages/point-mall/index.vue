<template>
  <view class="point-mall-page">
    <!-- 积分余额显示 -->
    <view class="balance-bar">
      <text class="label">可用积分</text>
      <text class="balance">{{ availablePoints || 0 }}</text>
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
          class="category-item"
          :class="{ active: selectedCategory === category }"
          v-for="category in categories"
          :key="category"
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
        class="product-item"
        v-for="product in products"
        :key="product.id"
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
          <text class="product-desc" v-if="product.description">
            {{ product.description }}
          </text>

          <view class="product-footer">
            <view class="stock-info">
              <text v-if="product.stock_unlimited" class="stock-unlimited">库存无限</text>
              <text v-else-if="product.stock > 0" class="stock-available">剩余{{ product.stock }}件</text>
              <text v-else class="stock-empty">已售罄</text>
            </view>
            <view class="price-tag">
              <text class="points">{{ product.points_cost }}</text>
              <text class="label">积分</text>
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

    // 提取分类
    const cats = new Set()
    products.value.forEach(p => {
      if (p.category) cats.add(p.category)
    })
    categories.value = Array.from(cats)
  } catch (err) {
    console.error('Failed to load products:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none'
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
    url: `/pages/point-mall/detail?id=${product.id}`
  })
}
</script>

<style lang="scss" scoped>
.point-mall-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.balance-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30rpx 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;

  .label {
    font-size: 26rpx;
    opacity: 0.9;
  }

  .balance {
    font-size: 40rpx;
    font-weight: bold;
  }
}

.category-filter {
  background: white;
  padding: 20rpx 0;
  margin-bottom: 20rpx;

  .category-scroll {
    white-space: nowrap;
    padding: 0 20rpx;

    .category-item {
      display: inline-block;
      padding: 10rpx 25rpx;
      margin-right: 15rpx;
      border-radius: 30rpx;
      font-size: 26rpx;
      background: #f5f5f5;
      color: #666;

      &.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
    }
  }
}

.loading,
.empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.products-list {
  padding: 20rpx;

  .product-item {
    display: flex;
    background: white;
    border-radius: 20rpx;
    overflow: hidden;
    margin-bottom: 20rpx;

    .product-image {
      width: 200rpx;
      height: 200rpx;
      flex-shrink: 0;

      &.placeholder {
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60rpx;
      }
    }

    .product-info {
      flex: 1;
      padding: 20rpx;
      display: flex;
      flex-direction: column;

      .product-name {
        font-size: 28rpx;
        font-weight: bold;
        margin-bottom: 10rpx;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
      }

      .product-desc {
        font-size: 24rpx;
        color: #999;
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
        margin-top: 15rpx;

        .stock-info {
          font-size: 22rpx;

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

        .price-tag {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 8rpx 20rpx;
          border-radius: 30rpx;
          display: flex;
          align-items: center;

          .points {
            font-size: 28rpx;
            font-weight: bold;
            margin-right: 5rpx;
          }

          .label {
            font-size: 20rpx;
            opacity: 0.9;
          }
        }
      }
    }
  }
}
</style>
