/**
 * 可取消的请求 composable
 *
 * 用于在组件卸载或需要时取消正在进行的请求
 * 防止内存泄漏和过时的响应覆盖新数据
 */
import { onUnmounted, ref } from 'vue'

export interface AbortableRequestOptions {
  /** 请求信号 */
  signal?: AbortSignal
}

/**
 * 使用可取消的请求
 *
 * @example
 * const { abort, createSignal, isAborted } = useAbortableRequest()
 *
 * async function fetchData() {
 *   const signal = createSignal()
 *   const data = await apiCall({ signal })
 * }
 *
 * onUnmounted(() => abort())
 */
export function useAbortableRequest() {
  const abortController = ref<AbortController | null>(null)
  const isAborted = ref(false)

  /**
   * 创建新的 AbortSignal
   * 如果之前有未完成的请求，会先取消它
   */
  function createSignal(): AbortSignal {
    // 取消之前的请求
    if (abortController.value !== null) {
      abortController.value.abort()
    }

    // 创建新的 AbortController
    abortController.value = new AbortController()
    isAborted.value = false

    return abortController.value.signal
  }

  /**
   * 取消当前请求
   */
  function abort() {
    if (abortController.value !== null) {
      abortController.value.abort()
      abortController.value = null
      isAborted.value = true
    }
  }

  /**
   * 重置状态
   */
  function reset() {
    abortController.value = null
    isAborted.value = false
  }

  // 组件卸载时自动取消请求
  onUnmounted(() => {
    abort()
  })

  return {
    abort,
    createSignal,
    isAborted,
    reset,
  }
}

/**
 * 防抖并取消之前的请求
 *
 * 结合了防抖和请求取消功能，适用于搜索、自动补全等场景
 *
 * @param delay 延迟时间（毫秒）
 * @returns 防抖的请求执行函数
 *
 * @example
 * const { run: debouncedFetch } = useDebounceRequest(500)
 *
 * watch(searchQuery, () => {
 *   debouncedFetch(async (signal) => {
 *     const data = await api.search(searchQuery.value, { signal })
 *     results.value = data
 *   })
 * })
 */
export function useDebounceRequest(delay: number = 300) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  let abortController: AbortController | null = null

  function run<T>(fn: (signal: AbortSignal) => Promise<T>): void {
    // 清除之前的定时器
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    // 取消之前的请求
    if (abortController !== null) {
      abortController.abort()
    }

    // 创建新的 AbortController
    abortController = new AbortController()
    // 在局部变量中捕获 signal，避免闭包中访问可能为 null 的 abortController
    const signal = abortController.signal

    // 设置延迟执行
    timeoutId = setTimeout(async () => {
      try {
        await fn(signal)
      } catch (error) {
        // 忽略 AbortError
        if (error instanceof Error && error.name === 'AbortError') {
          // 请求被取消，不做任何处理
        } else {
          // 其他错误正常抛出
          throw error
        }
      } finally {
        timeoutId = null
        abortController = null
      }
    }, delay)
  }

  /**
   * 取消待执行的请求
   */
  function cancel() {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
      timeoutId = null
    }

    if (abortController !== null) {
      abortController.abort()
      abortController = null
    }
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    cancel()
  })

  return {
    run,
    cancel,
  }
}
