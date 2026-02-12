<template>
  <div class="action-buttons" role="group" aria-label="操作按钮组">
    <el-button
      v-if="showEdit"
      link
      type="primary"
      size="small"
      aria-label="编辑"
      @click="$emit('edit')"
    >
      编辑
    </el-button>
    <el-button
      v-if="showToggle"
      link
      :type="isActive ? 'warning' : 'success'"
      size="small"
      :aria-label="isActive ? '禁用' : '启用'"
      @click="$emit('toggle')"
    >
      {{ isActive ? '禁用' : '启用' }}
    </el-button>
    <el-button
      v-if="showDelete"
      link
      type="danger"
      size="small"
      aria-label="删除"
      @click="$emit('delete')"
    >
      删除
    </el-button>
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
interface Props {
  showEdit?: boolean
  showToggle?: boolean
  showDelete?: boolean
  isActive?: boolean
}

withDefaults(defineProps<Props>(), {
  showEdit: true,
  showToggle: true,
  showDelete: true,
  isActive: true,
})

defineEmits(['edit', 'toggle', 'delete'])
</script>

<style scoped>
.action-buttons {
  display: flex;
  gap: var(--spacing-sm);
}
</style>
