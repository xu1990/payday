/**
 * 请求管理 composable - 自动取消未完成的请求
 * 修复：避免函数名shadow导入的request
 */
import { ref, onUnmounted, onScopeDisposed } from 'vue'
import type { RequestOptions } from '@/utils/request'
import { request as makeRequest } from '@/utils/request'

interface RequestState {
  loading: boolean
  error: string | null
}

export function useRequest() {
  const state = ref<RequestState>({
    loading: false,
    error: null,
  })

  // 当前活跃的请求ID（用于取消）
  let currentRequestId = 0
  let isCancelled = false

  /**
   * 清理函数：取消当前请求并重置状态
   */
  const cleanup = () => {
    isCancelled = true
    currentRequestId++
    state.value.loading = false
  }

  // 组件卸载时清理
  onUnmounted(cleanup)
  // scope销毁时也清理（例如v-if切换）
  onScopeDisposed(cleanup)

  /**
   * 执行请求，自动取消之前的未完成请求
   * 重命名函数避免与导入的request冲突
   */
  async function executeRequest<T>(options: RequestOptions): Promise<T> {
    // 如果已取消，直接拒绝
    if (isCancelled) {
      throw new Error('Request cancelled due to component unmount')
    }

    // 创建新的请求ID
    const requestId = ++currentRequestId
    state.value.loading = true
    state.value.error = null

    try {
      // 执行实际的请求（使用导入的makeRequest）
      const result = await makeRequest<T>(options)

      // 检查是否已被取消或已有新请求
      if (isCancelled || requestId !== currentRequestId) {
        throw new Error('Request cancelled')
      }

      state.value.loading = false
      return result
    } catch (e: unknown) {
      // 如果是取消错误，静默处理
      if (e instanceof Error && e.message === 'Request cancelled') {
        throw e
      }

      // 其他错误：更新状态
      state.value.loading = false
      const errorMessage = e instanceof Error ? e.message : '请求失败'
      state.value.error = errorMessage
      throw e
    } finally {
      // 确保最终状态正确
      if (requestId === currentRequestId) {
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
    isCancelled = false
    currentRequestId = 0
  }

  return {
    state,
    request: executeRequest, // 导出重命名后的函数
    cancel,
    reset,
  }
}
