<template>
  <view class="pd-empty">
    <view v-if="$slots.icon" class="pd-empty__icon">
      <slot name="icon" />
    </view>
    <text v-else class="pd-empty__default-icon">{{ defaultIcon }}</text>
    <text v-if="title" class="pd-empty__title">{{ title }}</text>
    <text v-if="description" class="pd-empty__description">{{ description }}</text>
    <view v-if="$slots.action" class="pd-empty__action">
      <slot name="action" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue'

const props = withDefaults(
  defineProps<{
    title?: string
    description?: string
    type?: 'default' | 'search' | 'network' | 'error'
  }>(),
  {
    title: '暂无数据',
    description: '',
    type: 'default',
  }
)

const $slots = useSlots()

const defaultIcon = computed(() => {
  const icons: Record<string, string> = {
    default: '📭',
    search: '🔍',
    network: '📡',
    error: '⚠️',
  }
  return icons[props.type]
})
</script>

<style lang="scss">
.pd-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;

  &__icon,
  &__default-icon {
    margin-bottom: 24rpx;
  }

  &__default-icon {
    font-size: 80rpx;
  }

  &__title {
    font-size: $font-size-lg;
    font-weight: $font-weight-medium;
    color: var(--text-secondary);
    margin-bottom: 12rpx;
  }

  &__description {
    font-size: $font-size-sm;
    color: var(--text-tertiary);
    text-align: center;
  }

  &__action {
    margin-top: 32rpx;
  }
}
</style>
