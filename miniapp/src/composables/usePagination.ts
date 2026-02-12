/**
 * 分页 composable - 统一分页逻辑
 */
import { ref, computed } from 'vue'

export interface PaginationOptions {
  pageSize?: number
  fetchFn: (params: { limit: number; offset: number }) => Promise<{
    items?: any[]
    total?: number
  } | void>
}

export function usePagination(options: PaginationOptions) {
  const { pageSize = 20, fetchFn } = options

  const loading = ref(false)
  const items = ref<any[]>([])
  const total = ref(0)
  const currentPage = ref(1)

  const hasMore = computed(() => items.value.length < total.value)

  /**
   * 加载数据
   */
  async function load() {
    loading.value = true
    try {
      const res = await fetchFn({
        limit: pageSize,
        offset: (currentPage.value - 1) * pageSize,
      })

      if (res) {
        items.value = res.items || []
        total.value = res.total || 0
      }
    } catch (e: unknown) {
      uni.showToast({
        title: e instanceof Error ? e.message : '加载失败',
        icon: 'none',
      })
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载更多
   */
  function loadMore() {
    if (!hasMore.value || loading.value) return
    currentPage.value++
    load()
  }

  /**
   * 刷新
   */
  function refresh() {
    currentPage.value = 1
    load()
  }

  /**
   * 重置分页
   */
  function reset() {
    currentPage.value = 1
    items.value = []
    total.value = 0
  }

  return {
    loading,
    items,
    total,
    currentPage,
    hasMore,
    load,
    loadMore,
    refresh,
    reset,
  }
}
