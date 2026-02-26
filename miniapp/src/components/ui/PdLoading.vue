<template>
  <view class="pd-loading" :class="{ 'pd-loading--fullpage': fullpage }">
    <view class="pd-loading__spinner" :class="{ 'ai-breathing': ai }">
      <view v-for="i in 3" :key="i" class="pd-loading__dot" :style="{ animationDelay: (i - 1) * 0.15 + 's' }" />
    </view>
    <text v-if="text" class="pd-loading__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string
    fullpage?: boolean
    ai?: boolean
  }>(),
  {
    text: '',
    fullpage: false,
    ai: false,
  }
)
</script>

<style lang="scss">
@keyframes loadingDot {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.pd-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;

  &--fullpage {
    position: fixed;
    inset: 0;
    background: var(--bg-base);
    z-index: 1000;
  }

  &__spinner {
    display: flex;
    gap: 12rpx;
  }

  &__dot {
    width: 16rpx;
    height: 16rpx;
    border-radius: 50%;
    background: $gradient-brand;
    animation: loadingDot 1.4s ease-in-out infinite;
  }

  &__text {
    margin-top: 20rpx;
    font-size: $font-size-sm;
    color: var(--text-secondary);
  }
}
</style>
