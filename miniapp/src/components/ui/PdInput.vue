<template>
  <view class="pd-input-wrapper">
    <view v-if="$slots.prefix" class="pd-input__prefix">
      <slot name="prefix" />
    </view>
    <input
      class="pd-input"
      :class="inputClasses"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxlength"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    />
    <view v-if="$slots.suffix" class="pd-input__suffix">
      <slot name="suffix" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, useSlots } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    type?: 'text' | 'number' | 'password' | 'tel'
    placeholder?: string
    disabled?: boolean
    maxlength?: number
    error?: boolean
  }>(),
  {
    modelValue: '',
    type: 'text',
    placeholder: '',
    disabled: false,
    error: false,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: Event]
  blur: [event: Event]
}>()

const $slots = useSlots()
const isFocused = ref(false)

const inputClasses = computed(() => [
  {
    'pd-input--focused': isFocused.value,
    'pd-input--disabled': props.disabled,
    'pd-input--error': props.error,
  },
])

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleFocus(event: Event) {
  isFocused.value = true
  emit('focus', event)
}

function handleBlur(event: Event) {
  isFocused.value = false
  emit('blur', event)
}
</script>

<style lang="scss">
.pd-input-wrapper {
  display: flex;
  align-items: center;
  @include glass-input();
}

.pd-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: inherit;
  color: inherit;

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--error {
    border-color: $semantic-error !important;
  }
}

.pd-input__prefix,
.pd-input__suffix {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
}

.pd-input__prefix {
  margin-right: 12rpx;
}

.pd-input__suffix {
  margin-left: 12rpx;
}
</style>
