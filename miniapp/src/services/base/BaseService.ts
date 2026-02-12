/**
 * 基础服务类 - 为所有服务提供统一的请求封装
 */
import { request } from '@/utils/request'

export abstract class BaseService {
  /**
   * 子类需要实现的基础 URL
   */
  protected abstract get baseUrl(): string

  /**
   * GET 请求
   */
  async get<T>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
    return request<T>({
      url: `${this.baseUrl}${endpoint}`,
      method: 'GET',
      data: params,
    })
  }

  /**
   * POST 请求
   */
  async post<T>(endpoint: string, data?: Record<string, unknown>): Promise<T> {
    return request<T>({
      url: `${this.baseUrl}${endpoint}`,
      method: 'POST',
      data,
    })
  }

  /**
   * PUT 请求
   */
  async put<T>(endpoint: string, data?: Record<string, unknown>): Promise<T> {
    return request<T>({
      url: `${this.baseUrl}${endpoint}`,
      method: 'PUT',
      data,
    })
  }

  /**
   * DELETE 请求
   */
  async delete<T>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
    return request<T>({
      url: `${this.baseUrl}${endpoint}`,
      method: 'DELETE',
      data: params,
    })
  }
}
