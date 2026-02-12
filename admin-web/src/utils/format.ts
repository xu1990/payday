/**
 * 格式化工具函数
 * 统一的日期、数字、状态格式化逻辑
 */

/**
 * 格式化日期时间
 * @param dateStr 日期字符串
 * @returns 格式化的日期时间，失败时返回原字符串
 */
export function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化日期时间
 * @param dateStr 日期字符串
 * @returns 格式化的日期时间，失败时返回原字符串
 */
export function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化时间
 * @param dateStr 时间字符串
 * @returns 格式化的时间，失败时返回原字符串
 */
export function formatTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化相对时间（如"3分钟前"）
 * @param dateStr 时间字符串
 * @returns 相对时间描述
 */
export function formatRelativeTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) {
      return `${days}天前`
    } else if (hours > 0) {
      return `${hours}小时前`
    } else if (minutes > 0) {
      return `${minutes}分钟前`
    } else {
      return '刚刚'
    }
  } catch {
    return dateStr
  }
}

/**
 * 格式化金额（分转元）
 * @param amountInCents 金额（分）
 * @returns 格式化的金额字符串
 */
export function formatAmount(amountInCents: number): string {
  if (typeof amountInCents !== 'number' || isNaN(amountInCents)) {
    return '¥0.00'
  }
  return (amountInCents / 100).toFixed(2)
}

/**
 * 格式化数字（添加千分位）
 * @param num 数字
 * @returns 格式化的数字字符串
 */
export function formatNumber(num: number): string {
  if (typeof num !== 'number' || isNaN(num)) {
    return '0'
  }
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '$1,')
}
