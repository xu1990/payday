/**
 * 格式化工具函数
 * 统一的日期、数字、状态格式化逻辑
 */

/**
 * 解析后端返回的时间字符串
 * 后端返回 UTC 时间但可能不带 'Z' 后缀，需要手动添加
 */
function parseBackendDate(dateStr: string): Date {
  // 如果时间字符串不包含时区信息（没有 Z、+、-），添加 'Z' 表示 UTC 时间
  if (!dateStr.match(/[Z+-]\d{2}:?\d{2}$/)) {
    return new Date(dateStr + 'Z')
  }
  return new Date(dateStr)
}

/**
 * 格式化日期 - 返回日期部分
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = parseBackendDate(dateStr)
    return date.toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化日期时间 - 返回完整日期时间
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = parseBackendDate(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化时间 - 只返回时间部分
 */
export function formatTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = parseBackendDate(dateStr)
    return date.toLocaleTimeString('zh-CN')
  } catch {
    return dateStr
  }
}

/**
 * 格式化金额 - 分转元
 */
export function formatAmount(amountInCents: number | null | undefined): string {
  if (typeof amountInCents !== 'number' || isNaN(amountInCents)) {
    return '¥0.00'
  }
  return '¥' + (amountInCents / 100).toFixed(2)
}

/**
 * 格式化数字 - 添加千分位
 */
export function formatNumber(num: number | null | undefined): string {
  if (typeof num !== 'number' || isNaN(num)) {
    return '0'
  }
  // SECURITY: 使用toLocaleString进行格式化，避免正则表达式错误
  // 自动处理千分位和本地化
  return num.toLocaleString('zh-CN')
}

/**
 * 格式化相对时间
 * 返回 "刚刚"、"5分钟前"、"2小时前" 等友好显示
 */
export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'

  try {
    const date = parseBackendDate(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (seconds < 60) {
      return '刚刚'
    } else if (minutes < 60) {
      return `${minutes}分钟前`
    } else if (hours < 24) {
      return `${hours}小时前`
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return formatDate(dateStr)
    }
  } catch {
    return dateStr
  }
}
