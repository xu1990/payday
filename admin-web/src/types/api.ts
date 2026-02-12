/**
 * 共享 API 类型定义
 * 集中管理所有API相关的类型定义，确保一致性
 */

/** API 错误响应 */
export interface ApiErrorResponse {
  response?: {
    data?: {
      detail?: string
      code?: string
    }
    status?: number
  }
  message?: string
}

/** API 响应 - 包含数据 */
export interface ApiResponse<T = {
  data: T
  message?: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit?: number
  offset?: number
}
