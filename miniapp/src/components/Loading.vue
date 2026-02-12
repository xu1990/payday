<template>
  <view v-if="show" class="page-loading-container" :class="{ fullscreen }">
    <view class="loading-content">
      <!-- 加载动画 -->
      <view v-if="type === 'spinner'" class="spinner">
        <view class="spinner-dot"></view>
        <view class="spinner-dot"></view>
        <view class="spinner-dot"></view>
      </view>

      <!-- 圆形进度条 -->
      <view v-else-if="type === 'circle'" class="circle-loading">
        <view class="circle-path"></view>
      </view>

      <!-- 文本提示 -->
      <text v-if="text" class="loading-text">{{ text }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  show?: boolean
  type?: 'spinner' | 'circle' | 'dots'
  text?: string
  fullscreen?: boolean
  backgroundColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  show: true,
  type: 'spinner',
  text: '',
  fullscreen: false,
  backgroundColor: 'rgba(255, 255, 255, 0.9)'
})
</script>

<style scoped>
.page-loading-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  background: transparent;
}

.page-loading-container.fullscreen {
  position: fixed;
  background: v-bind(backgroundColor);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
  padding: 40rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.fullscreen .loading-content {
  background: transparent;
  box-shadow: none;
}

/* Spinner 样式 */
.spinner {
  display: flex;
  gap: 12rpx;
}

.spinner-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #5470c6;
  animation: spinner-bounce 1.4s infinite ease-in-out both;
}

.spinner-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.spinner-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes spinner-bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 圆形加载样式 */
.circle-loading {
  width: 60rpx;
  height: 60rpx;
  position: relative;
}

.circle-path {
  width: 100%;
  height: 100%;
  border: 4rpx solid #f3f3f3;
  border-top-color: #5470c6;
  border-radius: 50%;
  animation: circle-spin 1s linear infinite;
}

@keyframes circle-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 28rpx;
  color: #666;
  text-align: center;
}
</style>
