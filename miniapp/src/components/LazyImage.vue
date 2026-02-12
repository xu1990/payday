<template>
  <view
    class="lazy-image-container"
    :style="{ width: props.width, height: props.height }"
  >
    <!-- 占位图/骨架屏 -->
    <view
      v-if="!isLoaded && !isError"
      class="lazy-skeleton"
      :style="{ backgroundColor: props.skeletonColor }"
    />

    <!-- 加载失败占位 -->
    <view
      v-if="isError"
      class="lazy-error"
      :style="{ width: props.width, height: props.height }"
      @click="handleRetry"
    >
      <text class="error-icon">⚠️</text>
      <text class="error-text">加载失败</text>
      <text class="error-retry">点击重试</text>
    </view>

    <!-- 实际图片 -->
    <image
      v-if="isLoaded"
      class="lazy-image"
      :src="displaySrc"
      :mode="props.mode"
      :lazy-load="true"
      :show-menu-by-longpress="props.showMenuByLongpress"
      @error="handleError"
      @load="handleLoad"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Props {
  src: string
  width?: string
  height?: string
  mode?: 'aspectFill' | 'aspectFit' | 'widthFix' | 'heightFix' | 'scaleToFill'
  skeletonColor?: string
  errorText?: string
  showMenuByLongpress?: boolean
  cache?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: 'auto',
  mode: 'aspectFill',
  skeletonColor: '#f5f5f5',
  errorText: '加载失败',
  showMenuByLongpress: false,
  cache: true,
})

const emit = defineEmits<{
  load: [e: any]
  error: [e: any]
  click: []
}>()

const isLoaded = ref(false)
const isError = ref(false)
const displaySrc = ref('')

// LRU 图片缓存实现（限制大小，防止内存泄漏）
const MAX_CACHE_SIZE = 100 // 最多缓存 100 张图片

class ImageCache {
  private cache = new Map<string, string>()

  get(key: string): string | undefined {
    const value = this.cache.get(key)
    if (value !== undefined) {
      // LRU: 删除后重新添加到末尾
      this.cache.delete(key)
      this.cache.set(key, value)
    }
    return value
  }

  set(key: string, value: string): void {
    // 如果缓存已满，删除最旧的条目（第一个）
    if (this.cache.size >= MAX_CACHE_SIZE && !this.cache.has(key)) {
      const firstKey = this.cache.keys().next().value
      if (firstKey) {
        this.cache.delete(firstKey)
      }
    }
    this.cache.set(key, value)
  }

  has(key: string): boolean {
    return this.cache.has(key)
  }

  clear(): void {
    this.cache.clear()
  }
}

// 创建全局缓存实例
const imageCache = new ImageCache()

// 预加载图片
onMounted(() => {
  if (props.cache) {
    const cached = imageCache.get(props.src)
    if (cached) {
      displaySrc.value = cached
      isLoaded.value = true
      return
    }
  }
  displaySrc.value = props.src
})

function handleLoad(e: any) {
  isLoaded.value = true
  isError.value = false

  // 缓存图片（使用 LRU 缓存）
  if (props.cache && !imageCache.has(props.src)) {
    imageCache.set(props.src, props.src)
  }

  emit('load', e)
}

function handleError(e: any) {
  isLoaded.value = false
  isError.value = true
  emit('error', e)
}

function handleRetry() {
  isError.value = false
  isLoaded.value = false
  displaySrc.value = props.src + '?t=' + Date.now()
}

function handleClick() {
  emit('click')
}

// 导出缓存清理方法，供外部使用
export function clearImageCache() {
  imageCache.clear()
}
</script>

<style scoped>
.lazy-image-container {
  position: relative;
  overflow: hidden;
  display: inline-block;
}

.lazy-skeleton {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.lazy-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  gap: 8rpx;
  cursor: pointer;
}

.error-icon {
  font-size: 48rpx;
}

.error-text {
  font-size: 24rpx;
  color: #999;
}

.error-retry {
  font-size: 22rpx;
  color: #5470c6;
}

.lazy-image {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
