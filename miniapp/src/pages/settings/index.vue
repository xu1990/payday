<template>
  <view class="settings-page">
    <view class="header">
      <text class="title">设置</text>
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
      <view class="setting-item" @click="handleAbout">
        <text class="setting-label">关于</text>
        <text class="setting-arrow">›</text>
      </view>
      <view class="setting-item" @click="handleFeedback">
        <text class="setting-label">反馈</text>
        <text class="setting-arrow">›</text>
      </view>
    </view>

    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUserSettings, updateUserSettings, type UserSettings } from '@/api/theme'

const settings = ref<UserSettings>({
  theme_id: null,
  privacy_profile: 0,
  allow_stranger_notice: 1,
  allow_comment: 1
})
const loading = ref(true)

onMounted(async () => {
  try {
    settings.value = await getUserSettings()
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

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

const goToThemes = () => {
  uni.navigateTo({ url: '/pages/themes/index' })
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
</script>

<style scoped>
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

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
