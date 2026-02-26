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
import { getMyAddresses, deleteAddress, setDefaultAddress } from '@/api/pointShop'

const loading = ref(false)
const addresses = ref([])
const selectMode = ref(false) // 是否为选择模式

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || {}
  selectMode.value = options.select === 'true'

  loadAddresses()
})

async function loadAddresses() {
  try {
    loading.value = true
    const res = await getMyAddresses(true)
    addresses.value = res.data?.items || []
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

<style scoped>
.addresses-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #eee;
}

.title {
  font-size: 32rpx;
  font-weight: 500;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 24rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
  color: #fff;
  font-size: 28rpx;
}

.add-btn .icon {
  font-size: 32rpx;
  line-height: 1;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 100rpx 0;
  color: #999;
}

.address-list {
  padding: 20rpx;
}

.address-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.address-content {
  margin-bottom: 20rpx;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.contact-name {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
}

.contact-phone {
  font-size: 28rpx;
  color: #666;
}

.default-badge {
  padding: 4rpx 12rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #fff;
}

.address-text {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

.address-actions {
  display: flex;
  gap: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #eee;
}

.action-btn {
  padding: 12rpx 24rpx;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #666;
  text-align: center;
}

.action-btn.delete {
  color: #f56c6c;
  border-color: #f56c6c;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.empty-btn {
  padding: 24rpx 60rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
  color: #fff;
  font-size: 28rpx;
}
</style>
