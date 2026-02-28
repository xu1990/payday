<template>
  <view class="login-page">
    <view class="login-container">
      <!-- Logo 区域 -->
      <view class="logo-section">
        <view class="logo-wrapper">
          <text class="logo-emoji">💰</text>
          <image class="logo" src="/static/logo.png" mode="aspectFit" />
        </view>
        <text class="app-name">薪日 PayDay</text>
        <text class="app-slogan">记录发薪日，分享打工心情</text>
      </view>

      <!-- 登录按钮 -->
      <view class="login-section">
        <!-- 邀请码输入（仅新用户显示） -->
        <view v-if="showInviteCodeInput" class="invite-code-section">
          <input
            v-model="inviteCode"
            class="invite-code-input"
            placeholder="请输入邀请码（选填）"
            maxlength="8"
          />
          <text class="invite-code-hint">填写邀请码，双方均可获得积分奖励</text>
        </view>

        <!-- 微信授权登录 -->
        <button
          class="login-btn"
          open-type="getPhoneNumber"
          :disabled="isLoading"
          @getphonenumber="handleWechatLogin"
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
import { getToken } from '@/utils/tokenStorage'
import { getQRCodeMapping } from '@/api/qrcode'

const authStore = useAuthStore()
const userStore = useUserStore()

const isLoading = ref(false)
const isChecking = ref(true)
const inviteCode = ref('')
const showInviteCodeInput = ref(false)

// 初始化检查登录状态和邀请码
onMounted(async () => {
  try {
    isChecking.value = true
    await authStore.init()

    if (authStore.isLoggedIn) {
      // 已登录，跳转到首页
      uni.reLaunch({
        url: '/pages/index',
      })
    } else {
      // 未登录，尝试获取邀请码参数
      const pages = getCurrentPages()
      const currentPage = pages[pages.length - 1]
      const pageOptions = (currentPage as any).options || {}

      // 如果URL中有邀请码参数，显示邀请码输入框并填充
      if (pageOptions.inviteCode) {
        inviteCode.value = pageOptions.inviteCode
        showInviteCodeInput.value = true
      }

      // 处理扫描二维码场景参数
      // scene 参数格式：微信小程序码扫描后会传入 scene 参数（短码）
      if (pageOptions.scene) {
        try {
          const shortCode = pageOptions.scene
          console.log('[login] Found scene parameter:', shortCode)

          // 调用后端 API 查询二维码映射
          const mapping = await getQRCodeMapping(shortCode)

          console.log('[login] QR code mapping response:', mapping)

          // 检查是否过期
          if (mapping.is_expired) {
            showError('二维码已过期')
          } else {
            // 从参数中提取邀请码
            if (mapping.params && mapping.params.inviteCode) {
              inviteCode.value = mapping.params.inviteCode
              showInviteCodeInput.value = true
              console.log('[login] Extracted invite code from QR code:', inviteCode.value)
            }
          }
        } catch (err) {
          console.error('[login] Failed to fetch QR code mapping:', err)
          // 即使获取映射失败，也不影响用户手动输入邀请码
        }
      }

      // 从本地缓存读取邀请码（如果有）
      const cachedInviteCode = uni.getStorageSync('pending_invite_code')
      if (cachedInviteCode) {
        inviteCode.value = cachedInviteCode
        showInviteCodeInput.value = true
        // 清除缓存，避免下次打开还显示
        uni.removeStorageSync('pending_invite_code')
      }
    }
  } catch (e) {
    console.error('[login] Init failed:', e)
  } finally {
    isChecking.value = false
  }
})

/**
 * 微信授权登录（获取手机号）
 */
async function handleWechatLogin(e: any) {
  if (isLoading.value) return

  console.log('[login] 手机号授权回调:', e)

  // 检查用户是否同意授权
  if (e.detail.errMsg !== 'getPhoneNumber:ok') {
    console.warn('[login] 用户拒绝授权手机号:', e.detail.errMsg)

    // 用户拒绝授权
    if (e.detail.errMsg.includes('cancel')) {
      console.info('[login] 用户取消授权')
      showError('已取消授权')
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

    console.log('[login] 开始微信授权登录...')

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

    // 调用后端登录接口（带手机号授权码和邀请码）
    console.log('[login] 开始调用后端登录接口...')
    const success = await authStore.login(
      loginRes.code,
      phoneNumberCode,
      inviteCode.value || undefined
    )

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
  background: $gradient-brand;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(40rpx + env(safe-area-inset-top)) 40rpx calc(40rpx + env(safe-area-inset-bottom));
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

.logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.2);
}

.logo-emoji {
  position: absolute;
  top: -16rpx;
  right: -16rpx;
  font-size: 48rpx;
  z-index: 1;
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
  width: 100%;
}

/* 邀请码输入区域 */
.invite-code-section {
  width: 100%;
  margin-bottom: 30rpx;
  padding: 30rpx;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20rpx;
  backdrop-filter: blur(10rpx);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
}

.invite-code-input {
  width: 100%;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: var(--text-primary);
  margin-bottom: 12rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.3);
  box-sizing: border-box;

  &::placeholder {
    color: var(--text-tertiary);
  }
}

.invite-code-hint {
  display: block;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  line-height: 1.4;
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
  color: var(--brand-primary);
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
