/**
 * 分页 Composable - 统一分页逻辑，减少代码重复
 *
 * 使用方式：
 * ```ts
 * import { usePagination } from '@/utils/usePagination'
 *
 * const { page, pageSize, setPagination, nextPage, prevPage } = usePagination(fetchData, total)
 * ```
 */
import { ref } from 'vue'
import type { Ref } from 'vue'

// 分页状态接口
interface PaginationState {
  page: number
  pageSize: number
  total: number
}

export function usePagination<T>(
  fetchFn: (params: { limit: number; offset: number }) => Promise<{ data: T[]; total: number }>,
  options?: {
    initialPageSize?: number
    immediate?: boolean
  }
) {
  const state = ref<PaginationState>({
    page: 1,
    pageSize: options?.initialPageSize || 20,
    total: 0,
  })

  // 设置分页
  const setPagination = (newPage: number) => {
    state.value.page = newPage
    state.value.pageSize = state.value.pageSize
  }

  // 下一页
  const nextPage = () => {
    if (state.value.page * state.value.pageSize >= state.value.total) {
      return // 已是最后一页
    }
    state.value.page++
  }

  // 上一页
  const prevPage = () => {
    if (state.value.page <= 1) {
      return // 已是第一页
    }
    state.value.page--
  }

  // 重置分页
  const reset = () => {
    state.value.page = 1
  }

  return {
    page: state.value.page,
    pageSize: state.value.pageSize,
    total: state.value.total,
    setPagination,
    nextPage,
    prevPage,
    reset,
  }
}
