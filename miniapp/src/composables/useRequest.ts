/**
 * 请求管理 composable - 自动取消未完成的请求
 */
import { ref, onUnmounted, onScopeDisposed } from 'vue'
import type { RequestOptions } from '@/utils/request'
import { request } from '@/utils/request'

interface RequestState {
  loading: boolean
  error: string | null
}

export function useRequest() {
  const state = ref<RequestState>({
    loading: false,
    error: null,
  })

  // uni.request 不支持 AbortController，所以用标志位模拟
  let currentTaskId = 0
  let cancelled = false

  /**
   * 清理函数：取消当前请求并重置状态
   */
  const cleanup = () => {
    cancelled = true
    currentTaskId++
    state.value.loading = false
  }

  // 组件卸载时清理
  onUnmounted(cleanup)
  // scope销毁时也清理（例如v-if切换）
  onScopeDisposed(cleanup)

  /**
   * 发起请求，自动取消之前的未完成请求
   */
  async function request<T>(options: RequestOptions): Promise<T> {
    // 如果已取消，直接拒绝
    if (cancelled) {
      throw new Error('Request cancelled due to component unmount')
    }

    // 取消之前的请求（通过递增 taskId）
    const taskId = ++currentTaskId
    state.value.loading = true
    state.value.error = null

    try {
      const result = await request<T>(options)

      // 检查是否已取消或已有新请求
      if (cancelled || taskId !== currentTaskId) {
        throw new Error('Request cancelled')
      }

      state.value.loading = false
      return result
    } catch (e: unknown) {
      // 如果是取消错误，不更新状态
      if (e instanceof Error && e.message === 'Request cancelled') {
        throw e
      }

      state.value.loading = false
      state.value.error = e instanceof Error ? e.message : '请求失败'
      throw e
    } finally {
      // 确保最终状态正确
      if (taskId === currentTaskId) {
        state.value.loading = false
      }
    }
  }

  /**
   * 手动取消当前请求
   */
  function cancel() {
    cleanup()
  }

  /**
   * 重置状态
   */
  function reset() {
    state.value = {
      loading: false,
      error: null,
    }
    cancelled = false
    currentTaskId = 0
  }

  return {
    state,
    request,
    cancel,
    reset,
  }
}
