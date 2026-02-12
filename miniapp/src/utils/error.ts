/**
 * 错误处理工具函数
 * 统一的错误类型判断和消息提取
 */

/**
 * 从未知错误对象中提取错误消息
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
 * 带响应状态的错误提取
 * 用于处理 API 返回的错误状态码
 */
export interface ErrorResponse {
  response?: {
    status?: number
    statusCode?: number
    data?: unknown
  }
}

/**
 * 根据响应状态码提取错误消息
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
 * 常见的 API 状态码消息映射
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
