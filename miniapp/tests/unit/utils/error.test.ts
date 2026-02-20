/**
 * error 工具函数测试
 */
import { describe, it, expect } from 'vitest'
import {
  getErrorMessage,
  getApiErrorMessage,
  commonStatusMessages,
  getCommonApiErrorMessage,
} from '@/utils/error'

describe('getErrorMessage', () => {
  it('应该从 Error 实例提取消息', () => {
    const error = new Error('Something went wrong')
    expect(getErrorMessage(error)).toBe('Something went wrong')
  })

  it('应该使用默认消息当 Error message 为空', () => {
    const error = new Error()
    expect(getErrorMessage(error, '默认错误')).toBe('默认错误')
  })

  it('应该处理字符串错误', () => {
    expect(getErrorMessage('Network error')).toBe('Network error')
  })

  it('应该使用默认消息当输入为空字符串', () => {
    // 空字符串被视为有效的错误消息
    expect(getErrorMessage('')).toBe('')
  })

  it('应该从对象中提取 message 属性', () => {
    const error = { message: 'Invalid input' }
    expect(getErrorMessage(error)).toBe('Invalid input')
  })

  it('应该使用默认消息当对象没有 message 属性', () => {
    const error = { code: 'ERROR' }
    expect(getErrorMessage(error, '默认错误')).toBe('默认错误')
  })

  it('应该使用默认消息当输入为 null', () => {
    expect(getErrorMessage(null, '默认错误')).toBe('默认错误')
  })

  it('应该使用默认消息当输入为 undefined', () => {
    expect(getErrorMessage(undefined, '默认错误')).toBe('默认错误')
  })

  it('应该使用默认消息当输入为空对象', () => {
    expect(getErrorMessage({}, '默认错误')).toBe('默认错误')
  })

  it('应该处理没有 message 的 Error', () => {
    const error = new Error()
    expect(getErrorMessage(error, '操作失败')).toBe('操作失败')
  })
})

describe('getApiErrorMessage', () => {
  it('应该根据状态码返回自定义消息', () => {
    const error = {
      response: {
        status: 404,
      },
    }
    const statusMessages = {
      404: '资源不存在',
    }
    expect(getApiErrorMessage(error, statusMessages)).toBe('资源不存在')
  })

  it('应该支持 statusCode 字段（uni.request 格式）', () => {
    const error = {
      response: {
        statusCode: 401,
      },
    }
    const statusMessages = {
      401: '未授权',
    }
    expect(getApiErrorMessage(error, statusMessages)).toBe('未授权')
  })

  it('应该返回默认消息当状态码未定义', () => {
    const error = {
      response: {
        status: 418,
      },
    }
    expect(getApiErrorMessage(error, {}, '未知错误')).toBe('未知错误')
  })

  it('应该回退到 getErrorMessage 当没有响应状态码', () => {
    const error = new Error('Network error')
    expect(getApiErrorMessage(error, {}, '操作失败')).toBe('Network error')
  })

  it('应该处理没有 response 属性的错误', () => {
    const error = { message: 'Request failed' }
    expect(getApiErrorMessage(error, {}, '操作失败')).toBe('Request failed')
  })
})

describe('commonStatusMessages', () => {
  it('应该包含所有常见状态码', () => {
    expect(commonStatusMessages[400]).toBe('请求参数错误')
    expect(commonStatusMessages[401]).toBe('未授权，请重新登录')
    expect(commonStatusMessages[403]).toBe('没有操作权限')
    expect(commonStatusMessages[404]).toBe('资源不存在')
    expect(commonStatusMessages[409]).toBe('操作冲突，请刷新后重试')
    expect(commonStatusMessages[422]).toBe('数据验证失败')
    expect(commonStatusMessages[429]).toBe('请求过于频繁，请稍后再试')
    expect(commonStatusMessages[500]).toBe('服务器内部错误')
    expect(commonStatusMessages[502]).toBe('网关错误')
    expect(commonStatusMessages[503]).toBe('服务暂时不可用')
  })

  it('应该有正确的状态码数量', () => {
    const keys = Object.keys(commonStatusMessages)
    expect(keys.length).toBe(10)
  })
})

describe('getCommonApiErrorMessage', () => {
  it('应该返回常见状态码的消息', () => {
    const error404 = { response: { status: 404 } }
    expect(getCommonApiErrorMessage(error404)).toBe('资源不存在')

    const error500 = { response: { status: 500 } }
    expect(getCommonApiErrorMessage(error500)).toBe('服务器内部错误')
  })

  it('应该处理未定义的状态码', () => {
    const error = { response: { status: 418 } }
    expect(getCommonApiErrorMessage(error)).toBe('操作失败')
  })

  it('应该回退到基本错误提取当没有状态码', () => {
    const error = new Error('Custom error')
    expect(getCommonApiErrorMessage(error)).toBe('Custom error')
  })
})
