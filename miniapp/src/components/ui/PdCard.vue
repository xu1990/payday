<template>
  <view :class="cardClasses" @click="handleClick">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    level?: 'subtle' | 'standard' | 'prominent'
    hoverable?: boolean
    padding?: 'none' | 'sm' | 'md' | 'lg'
  }>(),
  {
    level: 'standard',
    hoverable: false,
    padding: 'md',
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const cardClasses = computed(() => [
  'pd-card',
  `pd-card--${props.level}`,
  `pd-card--padding-${props.padding}`,
  {
    'pd-card--hoverable': props.hoverable,
  },
])

function handleClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<style lang="scss">
@import '@/styles/glass';

.pd-card {
  transition: all $transition-base $ease-out;

  &--subtle {
    background: var(--bg-glass-subtle);
    border: none;
  }

  &--standard {
    @include glass-card();
  }

  &--prominent {
    @include glass-card($prominent: true);
  }

  &--padding-none {
    padding: 0;
  }

  &--padding-sm {
    padding: 16rpx;
  }

  &--padding-md {
    padding: 24rpx;
  }

  &--padding-lg {
    padding: 32rpx;
  }

  &--hoverable {
    cursor: pointer;

    &:active {
      transform: scale(0.98);
      opacity: 0.95;
    }
  }
}
</style>
