<template>
  <el-tag :type="tagType" size="small" role="status" :aria-label="`状态：${displayText}`">
    {{ displayText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
interface Props {
  status: string
  statusMap?: Record<string, { text: string; type: 'success' | 'warning' | 'info' | 'danger' }>
}

const props = withDefaults(defineProps<Props>(), {
  statusMap: () => ({
    active: { text: '启用', type: 'success' },
    enabled: { text: '启用', type: 'success' },
    normal: { text: '正常', type: 'success' },
    paid: { text: '已支付', type: 'success' },
    approved: { text: '已通过', type: 'success' },
    disabled: { text: '禁用', type: 'warning' },
    inactive: { text: '未激活', type: 'info' },
    pending: { text: '待处理', type: 'info' },
    rejected: { text: '已拒绝', type: 'danger' },
    deleted: { text: '已删除', type: 'danger' },
    cancelled: { text: '已取消', type: 'info' },
  }),
})

const displayText = computed(() => {
  const text = props.statusMap[props.status]?.text || props.status
  // 额外防护：移除潜在的 HTML 标签
  return text.replace(/<[^>]*>/g, '')
})

const tagType = computed(() => {
  return props.statusMap[props.status]?.type || 'info'
})
</script>
