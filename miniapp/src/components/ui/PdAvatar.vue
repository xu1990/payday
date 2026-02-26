<template>
  <view :class="avatarClasses" @click="handleClick">
    <image
      v-if="src"
      class="pd-avatar__image"
      :src="src"
      mode="aspectFill"
    />
    <text v-else class="pd-avatar__fallback">{{ fallbackText }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    name?: string
    glass?: boolean
  }>(),
  {
    src: '',
    size: 'md',
    name: '',
    glass: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const avatarClasses = computed(() => [
  'pd-avatar',
  `pd-avatar--${props.size}`,
  {
    'pd-avatar--glass': props.glass,
    'pd-avatar--has-image': !!props.src,
  },
])

const fallbackText = computed(() => {
  if (!props.name) return '?'
  return props.name.charAt(0).toUpperCase()
})

function handleClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<style lang="scss">
@import '@/styles/glass';

.pd-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba($brand-primary, 0.15);
  color: var(--brand-primary);
  overflow: hidden;

  &--xs {
    width: 48rpx;
    height: 48rpx;
    font-size: $font-size-xs;
  }

  &--sm {
    width: 64rpx;
    height: 64rpx;
    font-size: $font-size-sm;
  }

  &--md {
    width: 88rpx;
    height: 88rpx;
    font-size: $font-size-lg;
  }

  &--lg {
    width: 120rpx;
    height: 120rpx;
    font-size: $font-size-xl;
  }

  &--xl {
    width: 160rpx;
    height: 160rpx;
    font-size: $font-size-2xl;
  }

  &--glass {
    border: 2rpx solid var(--border-glow);
    background: var(--bg-glass-standard);
    backdrop-filter: blur(10rpx);
  }

  &__image {
    width: 100%;
    height: 100%;
  }

  &__fallback {
    font-weight: $font-weight-semibold;
  }
}
</style>
