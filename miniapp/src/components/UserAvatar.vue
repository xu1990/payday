<script setup lang="ts">
interface Props {
  avatar: string | null | undefined
  anonymousName: string
  size?: 'small' | 'medium' | 'large'
}

withDefaults(defineProps<Props>(), {
  size: 'medium'
})
</script>

<template>
  <image
    v-if="avatar"
    :src="avatar"
    class="avatar"
    :class="size"
    mode="aspectFill"
  />
  <view v-else class="avatar-placeholder" :class="size">
    {{ anonymousName?.substring(0, 1) || '?' }}
  </view>
</template>

<style scoped>
.avatar {
  border-radius: 50%;
  background: #f0f0f0;
  flex-shrink: 0;
}

.avatar.small {
  width: 60rpx;
  height: 60rpx;
}

.avatar.medium {
  width: 80rpx;
  height: 80rpx;
}

.avatar.large {
  width: 100rpx;
  height: 100rpx;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #07c160;
  color: #fff;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.avatar-placeholder.small {
  width: 60rpx;
  height: 60rpx;
  font-size: 24rpx;
}

.avatar-placeholder.medium {
  width: 80rpx;
  height: 80rpx;
  font-size: 32rpx;
}

.avatar-placeholder.large {
  width: 100rpx;
  height: 100rpx;
  font-size: 36rpx;
}
</style>
