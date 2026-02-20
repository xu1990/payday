/**
 * 内容净化工具 - 防止 XSS 攻击
 *
 * 在小程序中，虽然 uni-app 对部分 XSS 有防护，
 * 但仍需对用户内容进行净化处理
 */

/**
 * 基础的 HTML 转义函数
 *
 * SECURITY: 转义 HTML 特殊字符，防止 XSS 攻击
 * 使用纯字符串替换，兼容小程序环境
 *
 * @param text - 待转义的文本
 * @returns 转义后的文本
 */
export function escapeHtml(text: string): string {
  const htmlEntities: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }

  return text.replace(/[&<>"']/g, char => htmlEntities[char])
}

/**
 * 净化用户生成的内容
 *
 * SECURITY: 移除潜在的危险内容
 * - HTML 标签
 * - JavaScript 协议
 * - 数据 URI
 *
 * @param content - 用户生成的内容
 * @param options - 净化选项
 * @returns 净化后的安全内容
 */
export function sanitizeContent(
  content: string,
  options: {
    maxLength?: number
    allowLineBreaks?: boolean
  } = {}
): string {
  const { maxLength = 10000, allowLineBreaks = true } = options

  // 截断到最大长度
  let sanitized = content.length > maxLength ? content.substring(0, maxLength) : content

  // 移除 HTML 标签（基础实现）
  // 注意：小程序环境对 HTML 渲染有限制，主要是移除脚本标签
  sanitized = sanitized.replace(/<script[^>]*>.*?<\/script>/gis, '')

  // 移除危险的协议（javascript:, data: 等）
  sanitized = sanitized.replace(/(javascript|data|vbscript):/gi, '')

  // 移除事件处理器
  sanitized = sanitized.replace(/on\w+\s*=/gi, '')

  // 转义 HTML 特殊字符
  sanitized = escapeHtml(sanitized)

  // 处理换行符
  if (!allowLineBreaks) {
    sanitized = sanitized.replace(/[\r\n]+/g, ' ')
  }

  return sanitized
}

/**
 * 净化用户昵称
 *
 * @param nickname - 用户昵称
 * @returns 净化后的昵称
 */
export function sanitizeNickname(nickname: string): string {
  // 昵称长度限制
  const MAX_NICKNAME_LENGTH = 50

  if (nickname.length > MAX_NICKNAME_LENGTH) {
    nickname = nickname.substring(0, MAX_NICKNAME_LENGTH)
  }

  // 移除所有 HTML 标签
  let sanitized = nickname.replace(/<[^>]*>/g, '')

  // 转义特殊字符
  sanitized = escapeHtml(sanitized)

  return sanitized
}

/**
 * 验证图片 URL 是否安全
 *
 * SECURITY: 防止恶意图片 URL（javascript:, data: 等）
 *
 * @param url - 图片 URL
 * @returns 是否为安全的图片 URL
 */
export function isValidImageUrl(url: string): boolean {
  if (!url) return false

  // 检查协议
  const lowerUrl = url.toLowerCase().trim()

  // 允许的协议
  const allowedProtocols = ['http://', 'https://']
  const hasAllowedProtocol = allowedProtocols.some(protocol => lowerUrl.startsWith(protocol))

  if (!hasAllowedProtocol) {
    return false
  }

  // 禁止的协议
  const blockedProtocols = ['javascript:', 'data:', 'vbscript:', 'file:']
  const hasBlockedProtocol = blockedProtocols.some(protocol => lowerUrl.startsWith(protocol))

  if (hasBlockedProtocol) {
    return false
  }

  return true
}

/**
 * 净化评论内容
 *
 * @param comment - 评论内容
 * @returns 净化后的评论
 */
export function sanitizeComment(comment: string): string {
  return sanitizeContent(comment, {
    maxLength: 1000,
    allowLineBreaks: true,
  })
}

/**
 * 净化帖子内容
 *
 * @param postContent - 帖子内容
 * @returns 净化后的帖子
 */
export function sanitizePost(postContent: string): string {
  return sanitizeContent(postContent, {
    maxLength: 10000,
    allowLineBreaks: true,
  })
}

/**
 * 移除控制字符（除了换行、制表符、回车）
 *
 * @param text - 待清理的文本
 * @returns 清理后的文本
 */
export function removeControlChars(text: string): string {
  return text.replace(/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/g, '')
}
