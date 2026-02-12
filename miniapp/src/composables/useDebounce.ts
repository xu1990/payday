/**
 * 防抖工具函数
 *
 * 用于防止函数在短时间内被频繁调用
 * 常用于搜索、tab 切换等场景
 */

import { ref } from 'vue'

/**
 * 创建防抖函数
 * @param fn 要防抖的函数
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的函数
 */
export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: Parameters<T>) {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      fn.apply(this, args)
      timeoutId = null
    }, delay)
  }
}

/**
 * 创建节流函数
 * @param fn 要节流的函数
 * @param delay 延迟时间（毫秒）
 * @returns 节流后的函数
 */
export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let lastCall = 0
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: Parameters<T>) {
    const now = Date.now()
    const remaining = delay - (now - lastCall)

    if (remaining <= 0) {
      // 可以立即执行
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
      lastCall = now
      fn.apply(this, args)
    } else if (!timeoutId) {
      // 设置延迟执行
      timeoutId = setTimeout(() => {
        lastCall = Date.now()
        timeoutId = null
        fn.apply(this, args)
      }, remaining)
    }
  }
}

/**
 * 防抖 composable
 * 用于在 Vue 组件中创建防抖的异步函数
 *
 * @example
 * const { run, loading } = useDebounceFn(async () => {
 *   await fetchData()
 * }, 500)
 */
export function useDebounceFn<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  delay: number = 300
) {
  const loading = ref(false)
  const timeoutId = ref<ReturnType<typeof setTimeout> | null>(null)

  const run = (...args: Parameters<T>): void => {
    if (timeoutId.value !== null) {
      clearTimeout(timeoutId.value)
    }

    loading.value = true
    timeoutId.value = setTimeout(async () => {
      try {
        await fn(...args)
      } finally {
        loading.value = false
        timeoutId.value = null
      }
    }, delay)
  }

  // 取消 pending 的调用
  const cancel = () => {
    if (timeoutId.value !== null) {
      clearTimeout(timeoutId.value)
      timeoutId.value = null
      loading.value = false
    }
  }

  return {
    run,
    loading,
    cancel,
  }
}
