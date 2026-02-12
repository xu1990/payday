<template>
  <div class="base-data-table">
    <el-table
      v-loading="loading"
      :data="items"
      stripe
      v-bind="$attrs"
      :aria-label="tableLabel"
    >
      <slot></slot>
    </el-table>

    <el-pagination
      v-if="showPagination"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      class="pagination"
      aria-label="分页控件"
      @current-change="handlePageChange"
      @size-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
import { onUnmounted } from 'vue'

interface Props<T = unknown> {
  items: T[]
  total: number
  loading: boolean
  showPagination?: boolean
  debounceMs?: number  // 防抖延迟（毫秒）
  tableLabel?: string  // 表格的可访问性标签
}

const emit = defineEmits(['page-change'])

const currentPage = defineModel<number>('currentPage', { default: 1 })
const pageSize = defineModel<number>('pageSize', { default: 20 })

// 存储props以便访问
const props = withDefaults(defineProps<Props<T>>(), {
  showPagination: true,
  debounceMs: 200,  // 默认 200ms 防抖
  tableLabel: '数据表格',
})

// 防抖分页变更
let debounceTimer: ReturnType<typeof setTimeout> | null = null

function handlePageChange() {
  // 如果有等待中的定时器，清除它
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }

  // 设置新的防抖定时器
  debounceTimer = setTimeout(() => {
    emit('page-change')
    debounceTimer = null
  }, props.debounceMs)
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }
})
</script>

<style scoped>
.base-data-table {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
