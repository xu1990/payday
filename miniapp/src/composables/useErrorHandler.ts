/**
 * 错误处理 composable - 统一错误处理逻辑
 */
import { ref } from 'vue'

export function useErrorHandler() {
  const error = ref<string | null>(null)

  /**
   * 处理错误
   */
  function handleError(e: unknown, showToast = true) {
    const message = e instanceof Error ? e.message : '操作失败'
    error.value = message

    if (showToast) {
      uni.showToast({
        title: message,
        icon: 'none',
        duration: 3000,
      })
    }
  }

  /**
   * 清除错误
   */
  function clearError() {
    error.value = null
  }

  return {
    error,
    handleError,
    clearError,
  }
}
