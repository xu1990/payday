/**
 * 错误处理工具函数
 * 统一的错误类型判断和消息提取
 */

/**
 * 从未知错误对象中提取错误消息
 * @param error - 错误对象（Error、字符串或对象）
 * @param defaultMessage - 默认错误消息
 * @returns 提取的错误消息字符串
 *
 * @example
 * getErrorMessage(new Error('Not found'), '操作失败') // 'Not found'
 * getErrorMessage('Network error', '加载失败') // 'Network error'
 * getErrorMessage({ message: 'Invalid input' }, '验证失败') // 'Invalid input'
 */
export function getErrorMessage(error: unknown, defaultMessage = '操作失败'): string {
  // 如果是 Error 实例，使用其 message
  if (error instanceof Error) {
    return error.message || defaultMessage
  }

  // 如果是字符串，直接使用
  if (typeof error === 'string') {
    return error
  }

  // 如果是对象且有 message 属性
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: string }).message) || defaultMessage
  }

  return defaultMessage
}

/**
 * 错误响应接口
 * 描述API响应中的错误结构（支持uni.request和axios格式）
 */
export interface ErrorResponse {
  response?: {
    status?: number
    statusCode?: number
    data?: unknown
  }
}

/**
 * 根据HTTP响应状态码提取错误消息
 * @param error - 错误对象
 * @param statusMessages - 状态码到消息的映射
 * @param defaultMessage - 默认错误消息
 * @returns 提取的错误消息字符串
 *
 * @example
 * getApiErrorMessage({ response: { status: 404 } }, { 404: '资源不存在' }) // '资源不存在'
 * getApiErrorMessage({ response: { status: 500 } }) // '服务器内部错误'
 */
export function getApiErrorMessage(
  error: unknown,
  statusMessages: Record<number, string>,
  defaultMessage = '操作失败'
): string {
  // 如果是 uni.request 错误响应
  const err = error as ErrorResponse

  const status = err.response?.status || err.response?.statusCode

  if (status) {
    return statusMessages[status] || statusMessages[Number(status)] || defaultMessage
  }

  // 否则使用默认错误提取
  return getErrorMessage(error, defaultMessage)
}

/**
 * 常见的HTTP状态码消息映射
 * 包含标准HTTP状态码对应的中文错误消息
 *
 * @example
 * ```ts
 * const status = 404
 * const message = commonStatusMessages[status] // '资源不存在'
 * ```
 */
export const commonStatusMessages: Record<number, string> = {
  400: '请求参数错误',
  401: '未授权，请重新登录',
  403: '没有操作权限',
  404: '资源不存在',
  409: '操作冲突，请刷新后重试',
  422: '数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务暂时不可用',
}

/**
 * 通用的 API 错误消息提取
 */
export function getCommonApiErrorMessage(error: unknown): string {
  return getApiErrorMessage(error, commonStatusMessages)
}
