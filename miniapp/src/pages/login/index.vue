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
    uni.reLaunch({
      url: '/pages/index'
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

    console.log('[login] 开始微信授权登录...')

    // 调用微信登录
    // 注意：微信小程序中 uni.login 不返回 [err, result] 格式
    const loginRes: any = await uni.login({
      provider: 'weixin'
    })

    console.log('[login] uni.login 结果:', loginRes)

    // 检查是否有错误 - errMsg 不是 "login:ok" 表示失败
    if (loginRes.errMsg && loginRes.errMsg !== 'login:ok') {
      const errMsg = loginRes.errMsg || ''
      console.error('[login] 微信登录失败:', loginRes)

      // 用户取消授权（不需要显示错误提示）
      if (errMsg.includes('cancel') || errMsg.includes('auth deny')) {
        console.info('[login] 用户取消授权')
        return
      }

      // 网络错误
      if (errMsg.includes('network') || errMsg.includes('timeout')) {
        showError('网络连接失败，请检查网络后重试')
        return
      }

      // 其他错误
      showError('微信登录失败：' + (errMsg || '未知错误'))
      return
    }

    if (!loginRes?.code) {
      console.error('[login] 未获取到微信授权码')
      showError('获取微信授权码失败，请重试')
      return
    }

    console.log('[login] 获取到微信授权码:', loginRes.code)

    // 调用后端登录接口
    console.log('[login] 开始调用后端登录接口...')
    const success = await authStore.login(loginRes.code)

    console.log('[login] 后端登录结果:', success)

    if (success) {
      showSuccess('登录成功')

      // 获取用户详细信息
      console.log('[login] 获取用户信息...')
      try {
        await userStore.fetchCurrentUser()
        console.log('[login] 用户信息获取成功')
      } catch (e) {
        console.warn('[login] 用户信息获取失败，但不影响登录:', e)
      }

      // 延迟跳转首页
      setTimeout(() => {
        uni.reLaunch({
          url: '/pages/index'
        })
      }, 500)
    } else {
      console.error('[login] 后端登录接口返回失败')
      showError('登录失败，请检查后端服务是否启动')
    }
  } catch (error: unknown) {
    console.error('[login] 登录过程抛出异常:', error)
    const message = error instanceof Error ? error.message : '登录失败，请重试'
    showError(message)
  } finally {
    isLoading.value = false
  }
}

/**
 * 跳转用户协议
 */
function goToUserAgreement() {
  uni.navigateTo({
    url: '/pages/user-agreement/index'
  })
}

/**
 * 跳转隐私政策
 */
function goToPrivacyPolicy() {
  uni.navigateTo({
    url: '/pages/privacy-policy/index'
  })
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
