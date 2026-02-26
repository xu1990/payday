<template>
  <view class="addresses-page">
    <!-- 顶部导航 -->
    <view class="header">
      <text class="title">收货地址</text>
      <view class="add-btn" @tap="goToAdd">
        <text class="icon">+</text>
        <text>新建地址</text>
      </view>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <!-- 地址列表 -->
    <view v-else-if="addresses.length > 0" class="address-list">
      <view
        v-for="address in addresses"
        :key="address.id"
        class="address-item"
        @tap="selectAddress(address)"
      >
        <view class="address-content">
          <view class="address-header">
            <text class="contact-name">{{ address.contact_name }}</text>
            <text class="contact-phone">{{ address.contact_phone }}</text>
            <view v-if="address.is_default" class="default-badge">默认</view>
          </view>
          <view class="address-text">
            <text>{{ address.province_name }}{{ address.city_name }}{{ address.district_name }}</text>
            <text>{{ address.detailed_address }}</text>
          </view>
        </view>
        <view class="address-actions" @tap.stop>
          <view class="action-btn" @tap="editAddress(address)">
            <text>编辑</text>
          </view>
          <view v-if="!address.is_default" class="action-btn" @tap="setDefault(address)">
            <text>设为默认</text>
          </view>
          <view class="action-btn delete" @tap="handleDeleteAddress(address)">
            <text>删除</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else class="empty-state">
      <text class="empty-icon">📍</text>
      <text class="empty-text">暂无收货地址</text>
      <button class="empty-btn" @tap="goToAdd">添加收货地址</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getMyAddresses, deleteAddress, setDefaultAddress } from '@/api/pointShop'

const loading = ref(false)
const addresses = ref([])
const selectMode = ref(false) // 是否为选择模式
const isInitialized = ref(false)

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || {}
  selectMode.value = options.select === 'true'

  loadAddresses()
  isInitialized.value = true
})

// 每次页面显示时刷新列表（从编辑页返回时自动刷新）
onShow(() => {
  if (isInitialized.value) {
    loadAddresses()
  }
})

async function loadAddresses() {
  try {
    loading.value = true
    const res = await getMyAddresses(true)
    addresses.value = res.items || []
  } catch (err) {
    console.error('Failed to load addresses:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function goToAdd() {
  uni.navigateTo({
    url: '/pages/point-mall/addresses/edit',
  })
}

function editAddress(address) {
  uni.navigateTo({
    url: `/pages/point-mall/addresses/edit?id=${address.id}`,
  })
}

function selectAddress(address) {
  if (!selectMode.value) return

  // 返回选中的地址
  const pages = getCurrentPages()
  const prevPage = pages[pages.length - 2]
  if (prevPage && prevPage.$vm) {
    prevPage.$vm.onAddressSelected?.(address)
  }
  uni.navigateBack()
}

async function setDefault(address) {
  try {
    uni.showLoading({ title: '设置中...' })
    await setDefaultAddress(address.id)
    uni.hideLoading()

    uni.showToast({
      title: '设置成功',
      icon: 'success',
    })

    await loadAddresses()
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: '设置失败',
      icon: 'none',
    })
  }
}

async function handleDeleteAddress(address) {
  const result = await uni.showModal({
    title: '确认删除',
    content: '确定要删除这个地址吗？',
  })

  if (!result.confirm) return

  try {
    uni.showLoading({ title: '删除中...' })
    await deleteAddress(address.id)
    uni.hideLoading()

    uni.showToast({
      title: '删除成功',
      icon: 'success',
    })

    await loadAddresses()
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: '删除失败',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.addresses-page {
  min-height: 100vh;
  background: var(--bg-base);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-lg;
  background: var(--bg-glass-standard);
  border-bottom: 1rpx solid var(--border-subtle);
}

.title {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm $spacing-lg;
  background: $gradient-brand;
  border-radius: $radius-full;
  color: #fff;
  font-size: $font-size-sm;
}

.add-btn .icon {
  font-size: $font-size-base;
  line-height: 1;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: $spacing-2xl 0;
  color: var(--text-tertiary);
}

.address-list {
  padding: $spacing-md;
}

.address-item {
  @include glass-card();
  border-radius: $radius-md;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.address-content {
  margin-bottom: $spacing-md;
}

.address-header {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-md;
}

.contact-name {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
}

.contact-phone {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.default-badge {
  padding: $spacing-xs $spacing-sm;
  background: $gradient-brand;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: #fff;
}

.address-text {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
  font-size: $font-size-sm;
  color: var(--text-secondary);
  line-height: 1.6;
}

.address-actions {
  display: flex;
  gap: $spacing-md;
  padding-top: $spacing-md;
  border-top: 1rpx solid var(--border-subtle);
}

.action-btn {
  padding: $spacing-sm $spacing-lg;
  border: 1rpx solid var(--border-regular);
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: var(--text-secondary);
  text-align: center;
}

.action-btn.delete {
  color: $semantic-error;
  border-color: $semantic-error;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-2xl 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: $spacing-md;
}

.empty-text {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
  margin-bottom: $spacing-lg;
}

.empty-btn {
  padding: $spacing-md $spacing-xl;
  background: $gradient-brand;
  border-radius: $radius-full;
  color: #fff;
  font-size: $font-size-sm;
}
</style>
