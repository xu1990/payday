<template>
  <view class="empty-state-container">
    <!-- 图标 -->
    <view class="empty-icon">
      <image v-if="icon" :src="icon" class="icon-image" mode="aspectFit" />
      <text v-else class="icon-text">{{ defaultIcon }}</text>
    </view>

    <!-- 文本 -->
    <text v-if="text" class="empty-text">{{ text }}</text>

    <!-- 描述 -->
    <text v-if="description" class="empty-description">{{ description }}</text>

    <!-- 操作按钮 -->
    <view v-if="actionText" class="empty-action">
      <button class="action-button" @click="handleAction">
        <text>{{ actionText }}</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  icon?: string
  text?: string
  description?: string
  actionText?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  action: []
}>()

// 默认图标
const defaultIcon = '📭'

function handleAction() {
  emit('action')
}
</script>

<style scoped>
.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 60rpx;
  text-align: center;
}

.empty-icon {
  margin-bottom: 32rpx;
}

.icon-image {
  width: 160rpx;
  height: 160rpx;
}

.icon-text {
  font-size: 120rpx;
  line-height: 1;
}

.empty-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}

.empty-description {
  font-size: 26rpx;
  color: #999;
  line-height: 1.6;
  max-width: 480rpx;
  display: block;
  margin-bottom: 40rpx;
}

.empty-action {
  margin-top: 20rpx;
}

.action-button {
  background: #5470c6;
  color: #fff;
  border: none;
  border-radius: 48rpx;
  padding: 20rpx 48rpx;
  font-size: 28rpx;
  line-height: 1;
}

.action-button:active {
  background: #455c9e;
}
</style>
