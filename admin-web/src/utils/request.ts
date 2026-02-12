/**
 * 统一的HTTP请求工具
 * 基于 adminApi 封装，提供一致的请求接口
 */
import { adminApi } from '@/api/admin'
import type { AxiosRequestConfig } from 'axios'

export interface RequestConfig extends AxiosRequestConfig {
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  data?: unknown
}

/**
 * 统一请求函数
 */
export function request<T>(config: RequestConfig) {
  const { url, method, data, params, ...rest } = config

  // 根据 method 选择对应的 axios 方法
  switch (method) {
    case 'GET':
      return adminApi.get<T>(url, { params, ...rest })
    case 'POST':
      return adminApi.post<T>(url, data, rest)
    case 'PUT':
      return adminApi.put<T>(url, data, rest)
    case 'DELETE':
      return adminApi.delete<T>(url, { params, ...rest })
    case 'PATCH':
      return adminApi.patch<T>(url, data, rest)
    default:
      throw new Error(`Unsupported method: ${method}`)
  }
}

// 导出 adminApi 实例供直接使用
export { adminApi }
