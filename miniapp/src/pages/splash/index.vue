<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const logoScale = ref(0)
const showText = ref(false)

onMounted(async () => {
  // Logo animation
  setTimeout(() => {
    logoScale.value = 1
  }, 100)

  // Show text animation
  setTimeout(() => {
    showText.value = true
  }, 500)

  // Check auth status and navigate
  try {
    await authStore.init()

    // Wait for animation to complete before navigating
    setTimeout(() => {
      if (authStore.isLoggedIn) {
        uni.switchTab({ url: '/pages/index' })
      } else {
        uni.redirectTo({ url: '/pages/login/index' })
      }
    }, 1800)
  } catch (e) {
    // On error, go to login after animation
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/login/index' })
    }, 1800)
  }
})
</script>

<template>
  <view class="splash-page">
    <view class="content">
      <!-- Logo/Icon -->
      <view class="logo-wrapper" :style="{ transform: `scale(${logoScale})` }">
        <view class="logo-icon">
          <text class="logo-text">¥</text>
        </view>
      </view>

      <!-- App Name -->
      <view class="app-name" :class="{ show: showText }">
        <text class="name-main">薪日 PayDay</text>
        <text class="name-sub">记录你的发薪时刻</text>
      </view>

      <!-- Loading dots -->
      <view class="loading-dots" :class="{ show: showText }">
        <view class="dot"></view>
        <view class="dot"></view>
        <view class="dot"></view>
      </view>
    </view>

    <!-- Copyright/Terms -->
    <view class="footer" :class="{ show: showText }">
      <text class="terms">登录即表示同意《用户协议》和《隐私政策》</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.splash-page {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 60rpx;
}

// Logo
.logo-wrapper {
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  margin-bottom: 60rpx;
}

.logo-icon {
  width: 160rpx;
  height: 160rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
  border: 4rpx solid rgba(255, 255, 255, 0.3);
}

.logo-text {
  font-size: 100rpx;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

// App name
.app-name {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0;
  transform: translateY(20rpx);
  transition: all 0.5s ease-out;

  &.show {
    opacity: 1;
    transform: translateY(0);
  }
}

.name-main {
  font-size: 52rpx;
  font-weight: 700;
  color: #fff;
  margin-bottom: 16rpx;
  letter-spacing: 4rpx;
}

.name-sub {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
}

// Loading dots
.loading-dots {
  display: flex;
  gap: 12rpx;
  margin-top: 80rpx;
  opacity: 0;
  transition: opacity 0.3s ease-out;

  &.show {
    opacity: 1;
  }
}

.dot {
  width: 16rpx;
  height: 16rpx;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;

  &:nth-child(1) {
    animation-delay: -0.32s;
  }

  &:nth-child(2) {
    animation-delay: -0.16s;
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.6;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

// Footer
.footer {
  position: absolute;
  bottom: 80rpx;
  left: 0;
  right: 0;
  padding: 0 60rpx;
  opacity: 0;
  transition: opacity 0.5s ease-out;

  &.show {
    opacity: 1;
  }
}

.terms {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  line-height: 1.6;
}
</style>
