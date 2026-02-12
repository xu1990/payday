<template>
  <div class="base-data-table">
    <el-table
      v-loading="loading"
      :data="items"
      stripe
      v-bind="$attrs"
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
      @current-change="handlePageChange"
      @size-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
interface Props<T = unknown> {
  items: T[]
  total: number
  loading: boolean
  showPagination?: boolean
}

const props = withDefaults(defineProps<Props<T>>(), {
  showPagination: true,
})

const emit = defineEmits(['page-change'])

const currentPage = defineModel<number>('currentPage', { default: 1 })
const pageSize = defineModel<number>('pageSize', { default: 20 })

function handlePageChange() {
  emit('page-change')
}
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
