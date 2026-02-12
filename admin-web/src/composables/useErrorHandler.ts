/**
 * 错误处理 composable
 * 提供统一的错误处理机制
 */
import { ElMessage } from 'element-plus'
import type { ApiErrorResponse } from '@/types/api'

export function useErrorHandler() {
  /**
   * 处理API错误并显示消息
   * @param error - 错误对象
   * @param fallbackMessage - 默认错误消息
   * @returns 错误消息字符串
   */
  const handleError = (error: unknown, fallbackMessage = '操作失败'): string => {
    const err = error as ApiErrorResponse
    const message = err.response?.data?.detail || err.message || fallbackMessage
    ElMessage.error(message)
    return message
  }

  /**
   * 安全地提取错误消息
   * @param error - 错误对象
   * @returns 错误消息或undefined
   */
  const getErrorMessage = (error: unknown): string | undefined => {
    const err = error as ApiErrorResponse
    return err.response?.data?.detail || err.message
  }

  /**
   * 检查是否是特定状态码的错误
   * @param error - 错误对象
   * @param status - HTTP状态码
   * @returns 是否匹配该状态码
   */
  const isStatusError = (error: unknown, status: number): boolean => {
    const err = error as ApiErrorResponse
    return err.response?.status === status
  }

  return {
    handleError,
    getErrorMessage,
    isStatusError,
  }
}
