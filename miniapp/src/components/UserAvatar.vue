<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  avatar: string | null | undefined
  anonymousName: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
})

// Validate avatar URL is from trusted source
function isValidAvatarUrl(url: string | null | undefined): boolean {
  if (!url) return false

  // Allow HTTPS URLs from trusted domains
  try {
    const u = new URL(url)

    // Must be HTTPS
    if (u.protocol !== 'https:') return false

    // Trusted domains (Tencent COS, QQ, etc.)
    const trustedDomains = [
      'cloud.tencent.com',
      'qq.com',
      'myqcloud.com',
      'qpic.cn', // QQ图片域名
      'wechat.com',
      // Add your CDN domain here if different
    ]

    return trustedDomains.some(
      domain => u.hostname === domain || u.hostname.endsWith('.' + domain),
    )
  } catch {
    return false
  }
}

const safeAvatar = computed(() => {
  return isValidAvatarUrl(props.avatar) ? props.avatar : null
})
</script>

<template>
  <image v-if="safeAvatar" :src="safeAvatar" class="avatar" :class="size" mode="aspectFill" />
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
