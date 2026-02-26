<template>
  <view class="image-carousel-wrapper">
    <swiper
      class="image-swiper"
      :indicator-dots="images.length > 1"
      :autoplay="autoplay"
      :interval="interval"
      :duration="duration"
      :circular="circular"
      indicator-color="rgba(255, 255, 255, 0.5)"
      indicator-active-color="#667eea"
      @change="onSwiperChange"
      @tap="onImageTap"
    >
      <swiper-item
        v-for="(image, index) in images"
        :key="index"
        class="swiper-item"
      >
        <image
          :src="image"
          mode="aspectFill"
          class="carousel-image"
          @tap.stop="previewImage(index)"
        />

        <!-- 图片序号 -->
        <view v-if="images.length > 1" class="image-counter">
          <text>{{ current + 1 }}/{{ images.length }}</text>
        </view>
      </swiper-item>
    </swiper>

    <!-- 缩略图导航 -->
    <view v-if="showThumbnails && images.length > 1" class="thumbnail-bar">
      <scroll-view scroll-x class="thumbnail-scroll">
        <view
          v-for="(image, index) in images"
          :key="index"
          class="thumbnail-item"
          :class="{ active: current === index }"
          @tap="goToSlide(index)"
        >
          <image
            :src="image"
            mode="aspectFill"
            class="thumbnail-image"
          />
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  images
  autoplay: {
    type
    default: false
  },
  interval: {
    type
    default: 3000
  },
  duration: {
    type
    default: 500
  },
  circular: {
    type
    default: true
  },
  showThumbnails: {
    type
    default: true
  }
})

const current = ref(0)

// 监听图片变化，重置当前索引
watch(() => props.images, () => {
  current.value = 0
})

function onSwiperChange(e) {
  current.value = e.detail.current
}

function goToSlide(index) {
  current.value = index
}

function onImageTap() {
  // 可以在这里处理点击事件
}

function previewImage(index) {
  if (props.images.length === 0) return

  uni.previewImage({
    urls: props.images,
    current: props.images[index],
  })
}

// 暴露方法供父组件调用
defineExpose({
  previewImage,
})
</script>

<style scoped>
.image-carousel-wrapper {
  position: relative;
  width: 100%;
  background-color: #fff;
}

.image-swiper {
  width: 100%;
  height: 750rpx;
}

.swiper-item {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.carousel-image {
  width: 100%;
  height: 100%;
}

.image-counter {
  position: absolute;
  bottom: 20rpx;
  right: 20rpx;
  padding: 8rpx 16rpx;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 20rpx;
  font-size: 22rpx;
  color: #fff;
}

/* 缩略图样式 */
.thumbnail-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16rpx 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.3), transparent);
}

.thumbnail-scroll {
  white-space: nowrap;
  padding: 0 20rpx;
}

.thumbnail-item {
  display: inline-block;
  width: 80rpx;
  height: 80rpx;
  margin-right: 12rpx;
  border-radius: 8rpx;
  overflow: hidden;
  border: 3rpx solid transparent;
  transition: all 0.3s;
  background-color: #f5f5f5;
}

.thumbnail-item.active {
  border-color: #667eea;
  transform: scale(1.1);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
}
</style>
