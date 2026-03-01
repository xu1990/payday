<template>
  <el-tag :type="tagType" size="small">
    {{ displayText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { PaymentMode } from '@/api/pointShop'

interface Props {
  mode: PaymentMode
}

const props = defineProps<Props>()

const displayText = computed(() => {
  switch (props.mode) {
    case 'points_only':
      return '纯积分'
    case 'cash_only':
      return '纯现金'
    case 'mixed':
      return '积分+现金'
    default:
      return props.mode
  }
})

const tagType = computed(() => {
  switch (props.mode) {
    case 'points_only':
      return 'success'
    case 'cash_only':
      return 'warning'
    case 'mixed':
      return 'primary'
    default:
      return 'info'
  }
})
</script>
