<template>
  <view class="login-page">
    <view class="login-container">
      <!-- Logo 区域 -->
      <view class="logo-section">
        <image class="logo" src="/static/logo.png" mode="aspectFit" />
        <text class="app-name">薪日 PayDay</text>
        <text class="app-slogan">记录发薪日，分享打工心情</text>
      </view>

      <!-- 登录按钮 -->
      <view class="login-section">
        <button
          class="login-btn"
          :disabled="isLoading"
          @tap="handleLogin"
        >
          <text v-if="!isLoading">微信授权登录</text>
          <text v-else>登录中...</text>
        </button>

        <!-- 用户协议 -->
        <view class="agreement">
          <text class="agreement-text">
            登录即表示同意
            <text class="link" @tap="goToUserAgreement">《用户协议》</text>
            和
            <text class="link" @tap="goToPrivacyPolicy">《隐私政策》</text>
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { showSuccess, showError } from '@/utils/toast'

const authStore = useAuthStore()
const userStore = useUserStore()

const isLoading = ref(false)

// 初始化检查登录状态
onMounted(() => {
  authStore.init()
  if (authStore.isLoggedIn) {
    // 已登录，跳转到首页
    uni.switchTab({
      url: '/pages/index/index'
    })
  }
})

/**
 * 微信授权登录
 */
async function handleLogin() {
  if (isLoading.value) return

  try {
    isLoading.value = true

    // 调用微信登录
    const loginRes = await uni.login({
      provider: 'weixin'
    })

    if (!loginRes[1].code) {
      showError('获取微信授权失败')
      return
    }

    // 调用后端登录接口
    const success = await authStore.login(loginRes[1].code)

    if (success) {
      showSuccess('登录成功')

      // 获取用户详细信息
      await userStore.fetchCurrentUser()

      // 延迟跳转首页
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/index/index'
        })
      }, 500)
    } else {
      showError('登录失败，请重试')
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    showError(error.message || '登录失败，请重试')
  } finally {
    isLoading.value = false
  }
}

/**
 * 跳转用户协议
 */
function goToUserAgreement() {
  // TODO: 实现用户协议页面
  showError('用户协议页面待实现')
}

/**
 * 跳转隐私政策
 */
function goToPrivacyPolicy() {
  // TODO: 实现隐私政策页面
  showError('隐私政策页面待实现')
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.login-container {
  width: 100%;
  max-width: 600rpx;
}

/* Logo 区域 */
.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 120rpx;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.2);
  margin-bottom: 40rpx;
}

.app-name {
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 16rpx;
}

.app-slogan {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

/* 登录区域 */
.login-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-btn {
  width: 100%;
  height: 96rpx;
  background: #ffffff;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #667eea;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.3);
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.2);
  }

  &[disabled] {
    opacity: 0.7;
  }
}

/* 协议 */
.agreement {
  margin-top: 40rpx;
  padding: 0 40rpx;
}

.agreement-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  text-align: center;
}

.link {
  color: #ffffff;
  text-decoration: underline;
}
</style>
