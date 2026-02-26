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

<style scoped lang="scss">
.themes-page {
  padding: $spacing-lg;
  background: var(--bg-base);
  min-height: 100vh;
}

.header {
  margin-bottom: $spacing-xl;
}

.title {
  font-size: $font-size-3xl;
  font-weight: $font-weight-bold;
  display: block;
}

.subtitle {
  font-size: $font-size-base;
  color: var(--text-secondary);
  display: block;
  margin-top: $spacing-xs;
}

.themes-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.theme-card {
  @include glass-card();
  display: flex;
  align-items: center;
  padding: $spacing-md;
  position: relative;
}

.theme-card.active {
  border: 4rpx solid $brand-primary;
}

.theme-preview {
  width: 100rpx;
  height: 100rpx;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: $spacing-md;
}

.theme-icon {
  font-size: $font-size-3xl;
}

.theme-info {
  flex: 1;
}

.theme-name {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  display: block;
  margin-bottom: $spacing-xs;
}

.theme-desc {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
  display: block;
}

.theme-check {
  width: 48rpx;
  height: 48rpx;
  background: $brand-primary;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-lg;
}

.loading {
  text-align: center;
  padding: $spacing-2xl;
  color: var(--text-tertiary);
}
</style>
