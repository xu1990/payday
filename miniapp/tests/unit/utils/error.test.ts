/**
 * 工具函数单元测试
 * 测试错误处理等工具函数
 */
import { describe, it, expect, vi } from 'vitest'
import { extractErrorMessage } from '@/utils/error'

describe('错误处理工具函数', () => {
  describe('extractErrorMessage', () => {
    it('应该提取 HTTP 错误消息', () => {
      const error = {
        response: {
          data: {
            message: '用户不存在',
            code: 'USER_NOT_FOUND',
          },
        },
      }

      const message = extractErrorMessage(error)
      expect(message).toBe('用户不存在')
    })

    it('应该处理网络错误', () => {
      const error = {
        message: 'Network Error',
      code: 'NETWORK_ERROR',
      }

      const message = extractErrorMessage(error)
      expect(message).toBe('网络错误，请检查网络连接')
    })

    it('应该处理超时错误', () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout',
      }

      const message = extractErrorMessage(error)
      expect(message).toBe('请求超时，请稍后重试')
    })

    it('应该返回默认错误消息', () => {
      const error = new Error('Unknown error')

      const message = extractErrorMessage(error)
      expect(message).toBe('操作失败，请稍后重试')
    })

    it('应该处理空错误', () => {
      const message = extractErrorMessage(null)
      expect(message).toBe('操作失败，请稍后重试')
    })
  })

  describe('HTTP 状态码映射', () => {
    it('应该正确映射 401 错误', () => {
      const error = {
        response: {
          status: 401,
          data: {
            message: '未授权',
          },
        },
      }

      const message = extractErrorMessage(error)
      expect(message).toContain('未授权')
    })

    it('应该正确映射 403 错误', () => {
      const error = {
        response: {
          status: 403,
          data: {
            message: '禁止访问',
          },
        },
      }

      const message = extractErrorMessage(error)
      expect(message).toContain('无权执行此操作')
    })

    it('应该正确映射 404 错误', () => {
      const error = {
        response: {
          status: 404,
        },
      }

      const message = extractErrorMessage(error)
      expect(message).toContain('不存在')
    })

    it('应该正确映射 500 错误', () => {
      const error = {
        response: {
          status: 500,
        },
      }

      const message = extractErrorMessage(error)
      expect(message).toContain('服务器错误')
    })
  })
})

/**
 * Mock 防抖函数测试
 */
import { useDebounce } from '@/utils/useDebounce'

describe('useDebounce 组合式函数', () => {
  vi.useFakeTimers()

  it('应该防抖函数调用', () => {
    let callCount = 0
    const debouncedFn = useDebounce(() => {
      callCount++
    }, 300)

    // 快速调用 5 次
    for (let i = 0; i < 5; i++) {
      debouncedFn()
    }

    expect(callCount).toBe(0)

    // 前进 300ms
    vi.advanceTimersByTime(300)

    expect(callCount).toBe(1)
  })

  it('应该取消之前的定时器', () => {
    let callCount = 0
    const debouncedFn = useDebounce(() => {
      callCount++
    }, 300)

    debouncedFn()
    vi.advanceTimersByTime(100)

    debouncedFn()
    vi.advanceTimersByTime(100)

    debouncedFn()
    vi.advanceTimersByTime(300)

    // 应该只调用一次
    expect(callCount).toBe(1)
  })

  it('应该立即执行如果 immediate 为 true', () => {
    let callCount = 0
    const debouncedFn = useDebounce(
      () => {
        callCount++
      },
      300,
      true,
    )

    debouncedFn()

    // 应该立即调用
    expect(callCount).toBe(1)

    vi.advanceTimersByTime(300)

    // 300ms 后不应该再次调用
    expect(callCount).toBe(1)
  })
})
