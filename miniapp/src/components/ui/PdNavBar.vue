<template>
  <view class="pd-navbar" :style="{ paddingTop: safeAreaTop + 'px' }">
    <view class="pd-navbar__content">
      <view class="pd-navbar__left" @click="handleBack">
        <slot name="left">
          <view v-if="showBack" class="pd-navbar__back">
            <text class="pd-navbar__back-icon">‹</text>
          </view>
        </slot>
      </view>
      <view class="pd-navbar__title">
        <slot>{{ title }}</slot>
      </view>
      <view class="pd-navbar__right">
        <slot name="right" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = withDefaults(
  defineProps<{
    title?: string
    showBack?: boolean
  }>(),
  {
    title: '',
    showBack: true,
  }
)

const emit = defineEmits<{
  back: []
}>()

const safeAreaTop = ref(0)

onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  safeAreaTop.value = systemInfo.safeAreaInsets?.top || 0
})

function handleBack() {
  if (props.showBack) {
    emit('back')
    uni.navigateBack()
  }
}
</script>

<style lang="scss">
.pd-navbar {
  @include glass-nav();
  position: sticky;
  top: 0;
  z-index: 100;

  &__content {
    display: flex;
    align-items: center;
    height: 88rpx;
    padding: 0 24rpx;
  }

  &__left,
  &__right {
    flex-shrink: 0;
    width: 80rpx;
  }

  &__title {
    flex: 1;
    text-align: center;
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__back {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56rpx;
    height: 56rpx;
    cursor: pointer;

    &:active {
      opacity: 0.7;
    }
  }

  &__back-icon {
    font-size: 48rpx;
    color: var(--text-primary);
    line-height: 1;
  }
}
</style>
