<template>
  <view class="settings-page">
    <view class="header">
      <text class="title">设置</text>
    </view>

    <!-- 个人资料 -->
    <view class="section profile-section">
      <view class="section-title">个人资料</view>

      <!-- 头像 -->
      <view class="setting-item avatar-item" @click="chooseAvatar">
        <text class="setting-label">头像</text>
        <view class="avatar-wrapper">
          <image
            class="avatar-image"
            :src="avatarUrl || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <text class="change-hint">点击更换</text>
        </view>
      </view>

      <!-- 昵称 -->
      <view class="setting-item">
        <text class="setting-label">昵称</text>
        <input
          v-model="nickname"
          class="nickname-input"
          placeholder="设置昵称"
          maxlength="20"
          @blur="saveNickname"
        />
      </view>
    </view>

    <!-- 隐私设置 -->
    <view class="section">
      <view class="section-title">隐私设置</view>

      <view class="setting-item">
        <text class="setting-label">公开个人资料</text>
        <switch
          :checked="settings.privacy_profile === 1"
          @change="handlePrivacyProfileChange"
          color="#5470c6"
        />
      </view>

      <view class="setting-item">
        <text class="setting-label">允许陌生人通知</text>
        <switch
          :checked="settings.allow_stranger_notice === 1"
          @change="handleStrangerNoticeChange"
          color="#5470c6"
        />
      </view>

      <view class="setting-item">
        <text class="setting-label">允许评论</text>
        <switch
          :checked="settings.allow_comment === 1"
          @change="handleCommentChange"
          color="#5470c6"
        />
      </view>
    </view>

    <!-- 主题设置 -->
    <view class="section">
      <view class="section-title">主题</view>
      <view class="setting-item" @click="goToThemes">
        <text class="setting-label">主题中心</text>
        <text class="setting-arrow">›</text>
      </view>
    </view>

    <!-- 其他 -->
    <view class="section">
      <view class="section-title">其他</view>
      <view class="setting-item" @click="handlePrivacyPolicy">
        <text class="setting-label">隐私协议</text>
        <text class="setting-arrow">›</text>
      </view>
      <view class="setting-item" @click="handleAbout">
        <text class="setting-label">关于</text>
        <text class="setting-arrow">›</text>
      </view>
      <view class="setting-item" @click="handleFeedback">
        <text class="setting-label">反馈</text>
        <text class="setting-arrow">›</text>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="section">
      <view class="section-title">退出登录</view>
      <button class="btn-logout" @click="handleLogout">退出登录</button>
    </view>

    <!-- 注销账号 -->
    <view class="section danger-section">
      <view class="section-title">账号操作</view>
      <button class="btn-deactivate" @click="handleDeactivate">注销账号</button>
      <text class="warning-text">⚠️ 注销后30天内可通过登录恢复</text>
    </view>

    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getUserSettings, updateUserSettings, type UserSettings } from '@/api/theme'
import { updateCurrentUser, deactivateAccount, logout } from '@/api/user'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const settings = ref<UserSettings>({
  theme_id: null,
  privacy_profile: 0,
  allow_stranger_notice: 1,
  allow_comment: 1
})
const loading = ref(true)

// 个人资料相关
const nickname = ref('')
const avatarUrl = ref('')

// 从 userStore 获取初始值
onMounted(async () => {
  try {
    settings.value = await getUserSettings()

    // 加载用户信息
    if (userStore.userInfo) {
      nickname.value = userStore.userInfo.nickname || ''
      avatarUrl.value = userStore.userInfo.avatar || ''
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

// 更新设置
const updateSetting = async (key: keyof UserSettingsUpdateReq, value: number | string | null) => {
  try {
    await updateUserSettings({ [key]: value })
    uni.showToast({ title: '设置已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

const handlePrivacyProfileChange = (e: any) => {
  settings.value.privacy_profile = e.detail.value ? 1 : 0
  updateSetting('privacy_profile', settings.value.privacy_profile)
}

const handleStrangerNoticeChange = (e: any) => {
  settings.value.allow_stranger_notice = e.detail.value ? 1 : 0
  updateSetting('allow_stranger_notice', settings.value.allow_stranger_notice)
}

const handleCommentChange = (e: any) => {
  settings.value.allow_comment = e.detail.value ? 1 : 0
  updateSetting('allow_comment', settings.value.allow_comment)
}

// 选择头像
async function chooseAvatar() {
  try {
    const res: any = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })

    if (res.tempFilePaths && res.tempFilePaths.length > 0) {
      const tempPath = res.tempFilePaths[0]

      // TODO: 这里需要上传图片到服务器
      // 暂时直接使用本地路径，实际需要调用上传接口
      avatarUrl.value = tempPath

      // 保存到服务器
      await saveProfile({ avatar: tempPath })
    }
  } catch (e) {
    // 用户取消选择
  }
}

// 保存昵称（失焦时触发）
async function saveNickname() {
  const trimmed = nickname.value.trim()
  if (!trimmed) {
    nickname.value = ''
    return
  }

  if (trimmed === (userStore.userInfo?.nickname || '')) {
    return // 没有变化
  }

  await saveProfile({ nickname: trimmed })
}

// 保存个人资料
async function saveProfile(data: { nickname?: string; avatar?: string }) {
  try {
    uni.showLoading({ title: '保存中...' })
    const updatedUser = await updateCurrentUser(data)

    // 更新 userStore
    await userStore.fetchCurrentUser()

    uni.hideLoading()
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' })

    // 恢复原值
    if (userStore.userInfo) {
      nickname.value = userStore.userInfo.nickname || ''
      avatarUrl.value = userStore.userInfo.avatar || ''
    }
  }
}

const goToThemes = () => {
  uni.navigateTo({ url: '/pages/themes/index' })
}

const handlePrivacyPolicy = () => {
  uni.navigateTo({ url: '/pages/privacy/index' })
}

const handleAbout = () => {
  uni.showModal({
    title: '关于薪日',
    content: '薪日 PayDay v1.0\n记录你的发薪日',
    showCancel: false
  })
}

const handleFeedback = () => {
  uni.showToast({ title: '反馈功能开发中', icon: 'none' })
}

// 退出登录
async function handleLogout() {
  try {
    await logout()

    // 清除本地存储
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('userInfo')

    // 清除 userStore
    userStore.$reset()

    uni.showToast({ title: '已退出登录', icon: 'success' })

    // 跳转到首页
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/index' })
    }, 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '退出失败', icon: 'none' })
  }
}

// 注销账号
async function handleDeactivate() {
  try {
    // 二次确认
    const confirmRes: any = await uni.showModal({
      title: '确认注销账号？',
      content: '注销后您的数据将被保留，30天内可通过登录恢复账号。超过30天将无法恢复。',
      confirmText: '确认注销',
      confirmColor: '#ff4d4f',
    })

    if (!confirmRes.confirm) {
      return
    }

    const res = await deactivateAccount()

    // 清除本地存储
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('userInfo')

    // 清除 userStore
    userStore.$reset()

    uni.showModal({
      title: '注销成功',
      content: `账号已注销，${new Date(res.data.recovery_until).toLocaleDateString()} 前可通过登录恢复`,
      showCancel: false,
      success: () => {
        uni.reLaunch({ url: '/pages/index' })
      }
    })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '注销失败', icon: 'none' })
  }
}
</script>

<style scoped lang="scss">
.settings-page {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  margin-bottom: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
  overflow: hidden;
}

.section-title {
  font-size: 28rpx;
  color: #999;
  padding: 24rpx 24rpx 16rpx;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 30rpx;
}

.setting-arrow {
  font-size: 48rpx;
  color: #999;
  font-weight: 300;
}

// 个人资料相关样式
.profile-section {
  .avatar-item {
    .avatar-wrapper {
      display: flex;
      align-items: center;
      gap: 16rpx;
    }

    .avatar-image {
      width: 80rpx;
      height: 80rpx;
      border-radius: 40rpx;
      background: #f0f0f0;
    }

    .change-hint {
      font-size: 24rpx;
      color: #667eea;
    }
  }

  .nickname-input {
    flex: 1;
    text-align: right;
    font-size: 28rpx;
    color: #333;
    padding: 8rpx 16rpx;
    border: 1rpx solid #e0e0e0;
    border-radius: 8rpx;
    min-width: 200rpx;
  }
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}

.btn-logout {
  width: 100%;
  background: #fff;
  color: #333;
  border: 1rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 30rpx;
  margin-top: 16rpx;
}

.danger-section {
  margin-top: 40rpx;
}

.btn-deactivate {
  width: 100%;
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  font-size: 30rpx;
  margin-top: 16rpx;
}

.warning-text {
  display: block;
  font-size: 24rpx;
  color: #ff4d4f;
  text-align: center;
  margin-top: 16rpx;
}
</style>
