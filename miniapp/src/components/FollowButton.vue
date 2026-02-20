<script setup lang="ts">
import { ref } from 'vue'
import { followUser, unfollowUser } from '@/api/follow'

interface Props {
  targetUserId: string
  isFollowing: boolean
  size?: 'default' | 'small' | 'large'
}

interface Emits {
  (e: 'follow', data: { targetUserId: string }): void
  (e: 'unfollow', data: { targetUserId: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
})

const emit = defineEmits<Emits>()
const loading = ref(false)

async function handleClick() {
  if (loading.value) return

  loading.value = true
  try {
    if (props.isFollowing) {
      await unfollowUser(props.targetUserId)
      emit('unfollow', { targetUserId: props.targetUserId })
      uni.showToast({ title: '已取消关注', icon: 'success' })
    } else {
      await followUser(props.targetUserId)
      emit('follow', { targetUserId: props.targetUserId })
      uni.showToast({ title: '关注成功', icon: 'success' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '操作失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view
    class="follow-btn"
    :class="[size, { following: isFollowing, loading }]"
    @tap="handleClick"
  >
    <text v-if="loading">加载中</text>
    <text v-else>{{ isFollowing ? '已关注' : '关注' }}</text>
  </view>
</template>

<style scoped>
.follow-btn {
  padding: 12rpx 32rpx;
  border-radius: 32rpx;
  font-size: 28rpx;
  font-weight: 500;
  background: #07c160;
  color: #fff;
  transition: all 0.2s;
}

.follow-btn.following {
  background: #f0f0f0;
  color: #666;
}

.follow-btn:disabled {
  opacity: 0.5;
}

.follow-btn.small {
  padding: 8rpx 24rpx;
  font-size: 24rpx;
}

.follow-btn.large {
  padding: 16rpx 40rpx;
  font-size: 32rpx;
}
</style>
