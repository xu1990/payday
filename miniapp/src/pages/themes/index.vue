<template>
  <view class="themes-page">
    <view class="header">
      <text class="title">主题中心</text>
      <text class="subtitle">选择你喜欢的主题</text>
    </view>

    <view class="themes-list">
      <view
        v-for="theme in themes"
        :key="theme.id"
        class="theme-card"
        :class="{ active: theme.id === currentThemeId }"
        @click="selectTheme(theme.id)"
      >
        <view class="theme-preview" :style="{ background: theme.preview_color }">
          <text class="theme-icon">🎨</text>
        </view>
        <view class="theme-info">
          <text class="theme-name">{{ theme.display_name }}</text>
          <text class="theme-desc">{{ theme.is_dark ? '深色主题' : '浅色主题' }}</text>
        </view>
        <view v-if="theme.id === currentThemeId" class="theme-check">
          <text>✓</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getThemes, getUserSettings, updateUserSettings } from '@/api/theme'

const themes = ref([])
const currentThemeId = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const [themesRes, settings] = await Promise.all([getThemes(), getUserSettings()])
    themes.value = themesRes.items
    currentThemeId.value = settings.theme_id
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

const selectTheme = async (themeId: string) => {
  try {
    await updateUserSettings({ theme_id: themeId })
    currentThemeId.value = themeId
    uni.showToast({ title: '主题已应用', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: '设置失败', icon: 'none' })
  }
}
</script>

<style scoped>
.themes-page {
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

.subtitle {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-top: 10rpx;
}

.themes-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.theme-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  position: relative;
}

.theme-card.active {
  border: 4rpx solid #5470c6;
}

.theme-preview {
  width: 100rpx;
  height: 100rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
}

.theme-icon {
  font-size: 48rpx;
}

.theme-info {
  flex: 1;
}

.theme-name {
  font-size: 32rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 8rpx;
}

.theme-desc {
  font-size: 24rpx;
  color: #999;
  display: block;
}

.theme-check {
  width: 48rpx;
  height: 48rpx;
  background: #5470c6;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
