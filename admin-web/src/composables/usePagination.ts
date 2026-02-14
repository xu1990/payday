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
    state.page = newPage
    state.pageSize = state.pageSize
  }

  // 下一页
  const nextPage = () => {
    if (state.page * state.pageSize >= state.total) {
      return // 已是最后一页
    }
    state.page++
  }

  // 上一页
  const prevPage = () => {
    if (state.page <= 1) {
      return // 已是第一页
    }
    state.page--
  }

  // 重置分页
  const reset = () => {
    state.page = 1
  }

  return {
    page: state.page,
    pageSize: state.pageSize,
    total: state.total,
    setPagination,
    nextPage,
    prevPage,
    reset,
  }
}
