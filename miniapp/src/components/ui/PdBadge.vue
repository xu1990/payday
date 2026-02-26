<template>
  <view :class="badgeClasses">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'
    size?: 'sm' | 'md'
    glass?: boolean
  }>(),
  {
    type: 'default',
    size: 'md',
    glass: false,
  }
)

const badgeClasses = computed(() => [
  'pd-badge',
  `pd-badge--${props.type}`,
  `pd-badge--${props.size}`,
  {
    'pd-badge--glass': props.glass,
  },
])
</script>

<style lang="scss">
@import '@/styles/glass';

.pd-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: $font-weight-medium;
  border-radius: 9999rpx;

  &--sm {
    padding: 4rpx 12rpx;
    font-size: $font-size-xs;
  }

  &--md {
    padding: 8rpx 20rpx;
    font-size: $font-size-sm;
  }

  &--default {
    background: rgba(0, 0, 0, 0.06);
    color: var(--text-secondary);
  }

  &--primary {
    background: rgba($brand-primary, 0.15);
    color: var(--brand-primary);
  }

  &--success {
    background: rgba($semantic-success, 0.15);
    color: $semantic-success;
  }

  &--error {
    background: rgba($semantic-error, 0.15);
    color: $semantic-error;
  }

  &--warning {
    background: rgba($semantic-warning, 0.15);
    color: $semantic-warning;
  }

  &--info {
    background: rgba($semantic-info, 0.15);
    color: $semantic-info;
  }

  &--glass {
    @include glass-card();
    backdrop-filter: blur(8rpx);

    &.pd-badge--primary {
      @include semantic-glass(rgba($brand-primary, 0.15));
    }

    &.pd-badge--success {
      @include semantic-glass(rgba($semantic-success, 0.15));
    }
  }
}
</style>
