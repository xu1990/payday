/**
 * 验证工具函数
 */

/**
 * 验证 URL 是否有效
 * 只允许 http 和 https 协议
 */
export function isValidUrl(url: string): boolean {
  if (!url) return true
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

/**
 * 清理 URL（移除危险字符）
 */
export function sanitizeUrl(url: string): string {
  if (!url) return ''
  const trimmed = url.trim()
  if (!isValidUrl(trimmed)) {
    return ''
  }
  return trimmed
}

/**
 * 验证字符串是否为空或仅空白
 */
export function isNotEmpty(value: string | null | undefined): boolean {
  return value !== null && value !== undefined && value.trim().length > 0
}

/**
 * 验证数字范围
 */
export function isInRange(value: number, min: number, max: number): boolean {
  return typeof value === 'number' && value >= min && value <= max
}

/**
 * 验证邮箱格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}
