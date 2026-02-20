<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const content = ref('')
const loading = ref(true)

async function loadAgreement() {
  try {
    const res: any = await request({
      url: '/api/v1/config/public/agreements',
      method: 'GET',
      noAuth: true, // 公开接口，无需鉴权
    })
    // request.ts 自动解包 details 字段
    console.log('[user-agreement] full response:', res)
    console.log('[user-agreement] user_agreement:', res?.user_agreement)
    // 兼容处理：如果解包失败，尝试从 details 中获取
    const agreement = res?.user_agreement || res?.details?.user_agreement || '暂无用户协议'
    console.log('[user-agreement] final content:', agreement)
    content.value = agreement
  } catch (e) {
    console.error('[user-agreement] error:', e)
    content.value = '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAgreement)
</script>

<template>
  <view v-if="!loading" class="legal-page">
    <view class="container">
      <view class="header">
        <text class="title">用户协议</text>
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
