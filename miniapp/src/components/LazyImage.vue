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

// 图片缓存Map（内存缓存，更高效）
const imageCache = new Map<string, string>()

// 预加载图片
onMounted(() => {
  if (props.cache) {
    if (imageCache.has(props.src)) {
      displaySrc.value = imageCache.get(props.src)!
      return
    }
  }
  displaySrc.value = props.src
})

function handleLoad(e: any) {
  isLoaded.value = true
  isError.value = false

  // 缓存图片（仅在未缓存时）
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
