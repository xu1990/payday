<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const content = ref('')
const loading = ref(true)

async function loadAgreement() {
  try {
    const res: any = await request({
      url: '/api/v1/config/public/agreements',
      method: 'GET'
    })
    content.value = res.data?.privacy_agreement || '暂无隐私政策'
  } catch (e) {
    content.value = '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAgreement)
</script>

<template>
  <view class="legal-page" v-if="!loading">
    <view class="container">
      <view class="header">
        <text class="title">隐私政策</text>
      </view>
      <view class="content">
        <rich-text :nodes="content"></rich-text>
      </view>
    </view>
  </view>
  <view v-else class="legal-page loading">
    <text>加载中...</text>
  </view>
</template>

<style scoped lang="scss">
.legal-page {
  min-height: 100vh;
  background-color: #f5f5f5;

  &.loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.container {
  padding: 40rpx;
}

.header {
  text-align: center;
  margin-bottom: 60rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
}

.content {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 40rpx;
  line-height: 1.8;
  font-size: 28rpx;
  color: #666;
}
</style>
