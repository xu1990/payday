/**
 * 统一的 Toast 提示工具
 */

type ToastType = 'success' | 'error' | 'loading' | 'none'

export interface ToastOptions {
  title?: string
  icon?: ToastType
  duration?: number
  mask?: boolean
  image?: string
}

/**
 * 显示提示
 */
export function showToast(options: ToastOptions): void {
  uni.showToast({
    title: options.title || '',
    icon: options.icon || 'none',
    duration: options.duration || 2000,
    mask: options.mask !== false,
    image: options.image,
  })
}

/**
 * 显示成功提示
 */
export function showSuccess(title: string, duration = 2000): void {
  showToast({ title, icon: 'success', duration })
}

/**
 * 显示错误提示
 */
export function showError(title: string, duration = 2000): void {
  showToast({ title, icon: 'error', duration })
}

/**
 * 显示加载提示
 */
export function showLoading(title = '加载中...', mask = true): void {
  uni.showLoading({ title, mask })
}

/**
 * 隐藏加载提示
 */
export function hideLoading(): void {
  uni.hideLoading()
}

/**
 * 显示普通提示
 */
export function showInfo(title: string, duration = 2000): void {
  showToast({ title, icon: 'none', duration })
}

export default {
  showToast,
  showSuccess,
  showError,
  showLoading,
  hideLoading,
  showInfo,
}
