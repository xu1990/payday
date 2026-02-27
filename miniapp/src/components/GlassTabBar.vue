<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'

interface TabItem {
  pagePath: string
  text: string
  icon: string
  activeIcon: string
}

const tabs: TabItem[] = [
  {
    pagePath: '/pages/index',
    text: '首页',
    icon: 'home',
    activeIcon: 'home-fill',
  },
  {
    pagePath: '/pages/square/index',
    text: '广场',
    icon: 'compass',
    activeIcon: 'compass-fill',
  },
  {
    pagePath: '/pages/feed/index',
    text: '关注',
    icon: 'heart',
    activeIcon: 'heart-fill',
  },
  {
    pagePath: '/pages/profile/index',
    text: '我的',
    icon: 'user',
    activeIcon: 'user-fill',
  },
]

// 立即获取当前页面路径（修复首页选中状态问题）
function getCurrentPath(): string {
  const pages = getCurrentPages()
  if (pages.length > 0) {
    const currentPage = pages[pages.length - 1]
    return '/' + currentPage.route
  }
  return '/pages/index'
}

const currentPath = ref(getCurrentPath())
const safeAreaBottom = ref(0)

// 获取系统安全区域
onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  safeAreaBottom.value = systemInfo.safeAreaInsets?.bottom || 0
  // 组件挂载时再次确认当前路径
  currentPath.value = getCurrentPath()
})

// 页面显示时更新当前路径
onShow(() => {
  currentPath.value = getCurrentPath()
})

const isActive = (path: string) => {
  // 标准化路径比较
  const normalizedCurrent = currentPath.value.replace(/\/index$/, '')
  const normalizedPath = path.replace(/\/index$/, '')
  return normalizedCurrent === normalizedPath
}

// 当前激活的索引（用于滑动动画）
const activeIndex = computed(() => {
  const normalizedCurrent = currentPath.value.replace(/\/index$/, '')
  const index = tabs.findIndex(tab => {
    const normalizedPath = tab.pagePath.replace(/\/index$/, '')
    return normalizedCurrent === normalizedPath
  })
  return index >= 0 ? index : 0
})

function switchTab(path: string) {
  if (isActive(path)) return

  uni.switchTab({
    url: path,
    fail: () => {
      // 如果 switchTab 失败，尝试 navigateTo
      uni.navigateTo({ url: path })
    },
  })
}

// 图标渲染
function getIconSvg(icon: string, filled: boolean) {
  const color = filled ? 'var(--brand-primary)' : 'var(--text-tertiary)'
  const icons: Record<string, string> = {
    home: `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    'home-fill': `<svg viewBox="0 0 24 24" fill="${color}"><path d="M12 2L2 12h3v8h6v-6h2v6h6v-8h3L12 2z"/></svg>`,
    compass: `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>`,
    'compass-fill': `<svg viewBox="0 0 24 24" fill="${color}"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.23 6.77l-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z"/></svg>`,
    heart: `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    'heart-fill': `<svg viewBox="0 0 24 24" fill="${color}"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    user: `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    'user-fill': `<svg viewBox="0 0 24 24" fill="${color}"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`,
  }
  return icons[icon] || ''
}
</script>

<template>
  <view class="glass-tabbar" :style="{ paddingBottom: safeAreaBottom + 'px' }">
    <!-- 背景光晕效果 -->
    <view class="tabbar-glow" />

    <!-- 玻璃容器 -->
    <view class="tabbar-container">
      <!-- 滑动背景指示器 -->
      <view
        class="slide-indicator"
        :style="{ left: activeIndex * 25 + '%', width: '25%' }"
      />

      <view
        v-for="(tab, index) in tabs"
        :key="tab.pagePath"
        class="tab-item"
        :class="{ active: isActive(tab.pagePath) }"
        @click="switchTab(tab.pagePath)"
      >
        <!-- 图标 -->
        <view class="tab-icon">
          <view
            class="icon-svg"
            v-html="getIconSvg(isActive(tab.pagePath) ? tab.activeIcon : tab.icon, isActive(tab.pagePath))"
          />
        </view>

        <!-- 文字 -->
        <text class="tab-text">{{ tab.text }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.glass-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}

.tabbar-glow {
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 300%;
  height: 300rpx;
  background: radial-gradient(
    ellipse 40% 100% at center bottom,
    rgba(74, 108, 247, 0.25) 0%,
    rgba(157, 123, 255, 0.15) 30%,
    rgba(74, 108, 247, 0.08) 50%,
    transparent 70%
  );
  pointer-events: none;
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
  50% {
    opacity: 0.7;
    transform: translateX(-50%) scale(1.05);
  }
}

.tabbar-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-around;
  margin: 0 24rpx 16rpx;
  padding: 12rpx 16rpx;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.45) 0%,
    rgba(255, 255, 255, 0.35) 50%,
    rgba(255, 255, 255, 0.45) 100%
  );
  backdrop-filter: blur(80rpx) saturate(200%);
  -webkit-backdrop-filter: blur(80rpx) saturate(200%);
  border-radius: 48rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.4);
  box-shadow:
    0 8rpx 32rpx rgba(0, 0, 0, 0.08),
    0 2rpx 8rpx rgba(0, 0, 0, 0.04),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.6);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8rpx 12rpx;
  position: relative;
  z-index: 1;
  transition: transform 0.2s ease;
}

.tab-item:active {
  transform: scale(0.92);
}

/* 滑动背景指示器 */
.slide-indicator {
  position: absolute;
  top: 8rpx;
  bottom: 8rpx;
  background: linear-gradient(
    135deg,
    rgba(74, 108, 247, 0.15) 0%,
    rgba(157, 123, 255, 0.1) 100%
  );
  border-radius: 32rpx;
  transition: left 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 0;
}

.tab-icon {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  z-index: 1;
}

.tab-item.active .tab-icon {
  transform: scale(1.15) translateY(-4rpx);
}

/* 文字弹跳动画 */
.tab-text {
  font-size: 20rpx;
  color: var(--text-tertiary);
  margin-top: 4rpx;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tab-item.active .tab-text {
  color: var(--brand-primary);
  font-weight: 600;
  transform: translateY(-2rpx);
}

.icon-svg {
  width: 44rpx;
  height: 44rpx;

  :deep(svg) {
    width: 100%;
    height: 100%;
  }
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .tabbar-container {
    background: linear-gradient(
      135deg,
      rgba(20, 25, 40, 0.5) 0%,
      rgba(25, 30, 50, 0.4) 50%,
      rgba(20, 25, 40, 0.5) 100%
    );
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow:
      0 8rpx 32rpx rgba(0, 0, 0, 0.3),
      0 2rpx 8rpx rgba(0, 0, 0, 0.2),
      inset 0 1rpx 0 rgba(255, 255, 255, 0.1);
  }

  .tabbar-glow {
    background: radial-gradient(
      ellipse 40% 100% at center bottom,
      rgba(94, 126, 248, 0.3) 0%,
      rgba(173, 143, 255, 0.15) 30%,
      rgba(94, 126, 248, 0.08) 50%,
      transparent 70%
    );
  }

  .slide-indicator {
    background: linear-gradient(
      135deg,
      rgba(94, 126, 248, 0.25) 0%,
      rgba(173, 143, 255, 0.15) 100%
    );
  }
}
</style>
