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
    <view class="loading-spinner"></view>
  </view>
</template>

<style scoped lang="scss">
.legal-page {
  min-height: 100vh;
  background: var(--bg-base);

  &.loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.container {
  padding: $spacing-2xl;
}

.header {
  text-align: center;
  margin-bottom: $spacing-3xl;
}

.title {
  display: block;
  font-size: $font-size-3xl;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
}

.content {
  @include glass-card();
  padding: $spacing-2xl;
  line-height: $line-height-relaxed;
  font-size: $font-size-base;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid var(--border-regular);
  border-top-color: var(--brand-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
