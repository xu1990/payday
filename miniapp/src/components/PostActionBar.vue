<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  postId: string
  likeCount: number
  commentCount: number
  viewCount?: number
  isLiked?: boolean
  compact?: boolean
  showView?: boolean
}

interface Emits {
  (e: 'like', data: { postId: string; isLiked: boolean }): void
  (e: 'comment', data: { postId: string }): void
  (e: 'share', data: { postId: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  viewCount: 0,
  isLiked: false,
  compact: false,
  showView: true,
})

const emit = defineEmits<Emits>()

const likeLoading = ref(false)

function handleLike() {
  if (likeLoading.value) return
  emit('like', { postId: props.postId, isLiked: props.isLiked })
}

function handleComment() {
  emit('comment', { postId: props.postId })
}

function handleShare() {
  emit('share', { postId: props.postId })
}
</script>

<template>
  <view class="action-bar" :class="{ compact }">
    <view
      class="action-btn"
      :class="{ liked: isLiked, loading: likeLoading }"
      @tap="handleLike"
    >
      <text class="icon">{{ isLiked ? '❤️' : '🤍' }}</text>
      <text class="count">{{ likeCount }}</text>
    </view>
    <view class="action-btn" @tap="handleComment">
      <text class="icon">💬</text>
      <text class="count">{{ commentCount }}</text>
    </view>
    <view v-if="showView && viewCount > 0" class="action-btn">
      <text class="icon">👁</text>
      <text class="count">{{ viewCount }}</text>
    </view>
    <view class="action-btn" @tap="handleShare">
      <text class="icon">⤴</text>
    </view>
  </view>
</template>

<style scoped>
.action-bar {
  display: flex;
  gap: 24rpx;
  padding: 16rpx 0;
  font-size: 24rpx;
  color: #666;
}

.action-bar.compact {
  padding: 12rpx 0;
  gap: 20rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  transition: background 0.2s;
}

.action-bar.compact .action-btn {
  padding: 6rpx 12rpx;
}

.action-btn:active {
  background: #f0f0f0;
}

.action-btn.liked {
  color: #ff4757;
}

.action-btn.loading {
  opacity: 0.5;
}

.icon {
  font-size: 28rpx;
}

.count {
  font-size: 24rpx;
}
</style>
