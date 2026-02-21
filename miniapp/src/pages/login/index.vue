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
        <!-- 快捷登录（无需手机号） -->
        <button class="login-btn login-btn-quick" :disabled="isLoading" @tap="handleQuickLogin">
          <text v-if="!isLoading">快捷登录</text>
          <text v-else>登录中...</text>
        </button>

        <!-- 手机号登录（需要授权） -->
        <button
          class="login-btn login-btn-phone"
          open-type="getPhoneNumber"
          :disabled="isLoading"
          @getphonenumber="handlePhoneLogin"
        >
          <text v-if="!isLoading">手机号登录</text>
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
const isChecking = ref(true)

// 初始化检查登录状态
onMounted(async () => {
  try {
    isChecking.value = true
    await authStore.init()

    if (authStore.isLoggedIn) {
      // 已登录，跳转到首页
      uni.reLaunch({
        url: '/pages/index',
      })
    }
  } catch (e) {
    console.error('[login] Init failed:', e)
  } finally {
    isChecking.value = false
  }
})

/**
 * 快捷登录（不授权手机号）
 */
async function handleQuickLogin() {
  if (isLoading.value) return

  try {
    isLoading.value = true

    console.log('[login] 开始快捷登录...')

    // 调用微信登录
    const loginRes: any = await uni.login({
      provider: 'weixin',
    })

    console.log('[login] uni.login 结果:', loginRes)

    // 检查是否有错误
    if (loginRes.errMsg && loginRes.errMsg !== 'login:ok') {
      const errMsg = loginRes.errMsg || ''
      console.error('[login] 微信登录失败:', loginRes)

      // 用户取消授权
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

    console.log('[login] 获取到微信授权码')

    // 调用后端登录接口（不带手机号）
    console.log('[login] 开始调用后端登录接口...')
    const success = await authStore.login(loginRes.code)

    console.log('[login] 后端登录结果:', success)

    if (success) {
      showSuccess('登录成功')

      // 不在登录页获取用户信息，由首页的 onShow 处理
      // 避免真机环境下 token 存储异步问题导致 401

      // 延迟跳转首页，确保 token 完全写入存储
      // 使用 reLaunch 而不是 switchTab，确保页面完全重新加载
      setTimeout(async () => {
        console.log('[login] 准备跳转到首页，先验证 token...')

        // 验证 token 是否确实存储成功
        const { getToken } = await import('@/utils/tokenStorage')
        const tokenCheck = await getToken()

        if (!tokenCheck) {
          console.error('[login] 跳转前验证失败：token未找到')
          showError('登录状态保存失败，请重试')
          return
        }

        console.log('[login] Token验证成功，准备跳转，length:', tokenCheck.length)

        // 使用 reLaunch 确保页面完全重新加载
        uni.reLaunch({
          url: '/pages/index',
        })
      }, 1000) // 增加延迟到 1000ms
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
 * 手机号登录（需要用户授权手机号）
 */
async function handlePhoneLogin(e: any) {
  if (isLoading.value) return

  console.log('[login] 手机号授权回调:', e)

  // 检查用户是否同意授权
  if (e.detail.errMsg !== 'getPhoneNumber:ok') {
    console.warn('[login] 用户拒绝授权手机号:', e.detail.errMsg)

    // 用户拒绝授权
    if (e.detail.errMsg.includes('cancel')) {
      console.info('[login] 用户取消手机号授权')
      showError('已取消手机号授权')
      return
    }

    // 其他错误
    showError('获取手机号失败：' + e.detail.errMsg)
    return
  }

  // 获取手机号授权码
  const phoneNumberCode = e.detail.code
  if (!phoneNumberCode) {
    console.error('[login] 未获取到手机号授权码')
    showError('获取手机号授权码失败，请重试')
    return
  }

  console.log('[login] 获取到手机号授权码')

  try {
    isLoading.value = true

    console.log('[login] 开始手机号登录...')

    // 调用微信登录获取登录授权码
    const loginRes: any = await uni.login({
      provider: 'weixin',
    })

    console.log('[login] uni.login 结果:', loginRes)

    // 检查是否有错误
    if (loginRes.errMsg && loginRes.errMsg !== 'login:ok') {
      const errMsg = loginRes.errMsg || ''
      console.error('[login] 微信登录失败:', loginRes)

      // 用户取消授权
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

    console.log('[login] 获取到微信授权码')

    // 调用后端登录接口（带手机号授权码）
    console.log('[login] 开始调用后端登录接口（带手机号）...')
    const success = await authStore.login(loginRes.code, phoneNumberCode)

    console.log('[login] 后端登录结果:', success)

    if (success) {
      showSuccess('登录成功')

      // 不在登录页获取用户信息，由首页的 onShow 处理
      // 避免真机环境下 token 存储异步问题导致 401

      // 延迟跳转首页，确保 token 完全写入存储
      setTimeout(() => {
        console.log('[login] 跳转到首页')
        uni.switchTab({
          url: '/pages/index',
        })
      }, 800)
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
    url: '/pages/user-agreement/index',
  })
}

/**
 * 跳转隐私政策
 */
function goToPrivacyPolicy() {
  uni.navigateTo({
    url: '/pages/privacy-policy/index',
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
  margin-bottom: 24rpx;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.2);
  }

  &[disabled] {
    opacity: 0.7;
  }

  &.login-btn-phone {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #ffffff;
    border: 2rpx solid rgba(255, 255, 255, 0.3);

    &:active {
      background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
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
