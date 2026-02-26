<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    :loading="loading"
    @click="handleClick"
  >
    <view v-if="loading" class="pd-btn__loading">
      <view class="pd-btn__spinner" />
    </view>
    <slot v-else />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'outline' | 'link' | 'glass'
    size?: 'sm' | 'md' | 'lg'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
    block: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClasses = computed(() => [
  'pd-btn',
  `pd-btn--${props.variant}`,
  `pd-btn--${props.size}`,
  {
    'pd-btn--block': props.block,
    'pd-btn--loading': props.loading,
  },
])

function handleClick(event: MouseEvent) {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style lang="scss">
.pd-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  font-weight: $font-weight-medium;
  transition: all $transition-base $ease-out;
  cursor: pointer;

  &--sm {
    padding: 12rpx 24rpx;
    font-size: $font-size-sm;
    border-radius: 8rpx;
  }

  &--md {
    padding: 20rpx 40rpx;
    font-size: $font-size-base;
    border-radius: 12rpx;
  }

  &--lg {
    padding: 28rpx 56rpx;
    font-size: $font-size-lg;
    border-radius: 16rpx;
  }

  &--primary {
    background: $gradient-brand;
    color: #fff;

    &:active {
      opacity: 0.9;
      transform: scale(0.97);
    }
  }

  &--secondary {
    background: $brand-secondary;
    color: #fff;

    &:active {
      opacity: 0.9;
      transform: scale(0.97);
    }
  }

  &--outline {
    background: transparent;
    color: var(--brand-primary);
    border: 1rpx solid var(--brand-primary);

    &:active {
      background: rgba($brand-primary, 0.1);
      transform: scale(0.97);
    }
  }

  &--link {
    background: transparent;
    color: var(--brand-primary);
    padding: 0;

    &:active {
      opacity: 0.7;
    }
  }

  &--glass {
    @include glass-card();
    color: var(--text-primary);

    &:active {
      transform: scale(0.97);
    }
  }

  &--block {
    display: flex;
    width: 100%;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--loading {
    pointer-events: none;
  }

  &__loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__spinner {
    width: 32rpx;
    height: 32rpx;
    border: 3rpx solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}
</style>
