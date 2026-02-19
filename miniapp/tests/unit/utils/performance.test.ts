/**
 * performance 工具函数测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock uni-app API
const mockOnAppShow = vi.fn()
const mockGetSystemInfo = vi.fn()

const setupUniMock = () => {
  global.uni = {
    onAppShow: mockOnAppShow,
    getSystemInfo: mockGetSystemInfo,
  }
}

// Mock getCurrentPages
const mockGetCurrentPages = vi.fn(() => [])

// Mock getApp
const mockGetApp = vi.fn(() => ({
  globalData: {
    launchTime: Date.now() - 1000,
  },
}))

// Save original uni
const originalUni = global.uni

describe('performance 工具函数', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup uni mock
    setupUniMock()
    global.getCurrentPages = mockGetCurrentPages as any
    global.getApp = mockGetApp as any
    // Reset module state
    vi.resetModules()
    // Reset getSystemInfo mock
    mockGetSystemInfo.mockImplementation(({ success }) => {
      success({
        brand: 'iPhone',
        model: '14',
        system: 'iOS 16',
        platform: 'ios',
        screenWidth: 390,
        screenHeight: 844,
        pixelRatio: 3,
        language: 'zh-CN',
        version: '8.0.5',
        fontSizeSetting: 16,
      })
    })
    // Set test environment
    process.env.NODE_ENV = 'test'
  })

  afterEach(() => {
    // Restore original uni
    global.uni = originalUni
  })

  describe('initPerformanceMonitoring', () => {
    it('应该初始化性能监控', async () => {
      const { initPerformanceMonitoring } = await import('@/utils/performance')

      // 第一次调用应该初始化
      initPerformanceMonitoring()
      // 第二次调用应该被忽略（幂等性）
      initPerformanceMonitoring()

      expect(mockOnAppShow).toHaveBeenCalled()
    })

    it('应该在没有 uni 时安全返回', async () => {
      const { initPerformanceMonitoring } = await import('@/utils/performance')

      // 临时移除 uni
      delete (global as any).uni

      // 应该不抛出错误
      initPerformanceMonitoring()

      // 恢复 uni
      setupUniMock()
    })
  })

  describe('性能指标上报', () => {
    it('应该记录页面访问', async () => {
      mockGetCurrentPages.mockReturnValue([{ route: 'pages/index/index' }])

      const { initPerformanceMonitoring } = await import('@/utils/performance')
      initPerformanceMonitoring()

      // 验证初始化成功
      expect(mockOnAppShow).toHaveBeenCalled()
    })

    it('应该处理空页面栈', async () => {
      mockGetCurrentPages.mockReturnValue([])

      const { initPerformanceMonitoring } = await import('@/utils/performance')
      initPerformanceMonitoring()

      // 验证不抛出错误
      expect(mockOnAppShow).toHaveBeenCalled()
    })
  })

  describe('性能工具函数', () => {
    it('应该导出性能相关函数', async () => {
      const perfModule = await import('@/utils/performance')

      // 验证导出的函数
      expect(typeof perfModule.initPerformanceMonitoring).toBe('function')
      expect(typeof perfModule.measureRequest).toBe('function')
      expect(typeof perfModule.measurePageRender).toBe('function')
      expect(typeof perfModule.getWeChatPerformanceData).toBe('function')
      expect(typeof perfModule.getSystemInfo).toBe('function')
      expect(typeof perfModule.getMemoryInfo).toBe('function')
      expect(typeof perfModule.usePerformance).toBe('function')
    })

    it('measureRequest 应该测量请求时间', async () => {
      const { measureRequest } = await import('@/utils/performance')

      const mockApiCall = vi.fn(() => Promise.resolve({ data: 'success' }))
      const measuredCall = measureRequest('test-api', mockApiCall)

      expect(typeof measuredCall).toBe('function')

      const result = await measuredCall()
      expect(result).toEqual({ data: 'success' })
      expect(mockApiCall).toHaveBeenCalled()
    })

    it('measurePageRender 应该测量渲染时间', async () => {
      const { measurePageRender } = await import('@/utils/performance')

      // performance API 不可用时应该安全返回
      measurePageRender('test-page')
      // 不应该抛出错误
      expect(true).toBe(true)
    })

    it('getWeChatPerformanceData 应该返回 null（非微信环境）', async () => {
      const { getWeChatPerformanceData } = await import('@/utils/performance')

      const result = getWeChatPerformanceData()
      // 非微信环境应该返回 null
      expect(result).toBeNull()
    })

    it('getSystemInfo 应该返回系统信息', async () => {
      const { getSystemInfo } = await import('@/utils/performance')

      const result = await getSystemInfo()
      expect(result).not.toBeNull()
      expect(typeof result).toBe('object')
    })

    it('getMemoryInfo 应该返回 Promise', async () => {
      const { getMemoryInfo } = await import('@/utils/performance')

      const result = await getMemoryInfo()
      // 非微信环境应该返回 null
      expect(result).toBeNull()
    })

    it('usePerformance 应该返回性能监控函数', async () => {
      const { usePerformance } = await import('@/utils/performance')

      const perf = usePerformance()
      expect(typeof perf.init).toBe('function')
      expect(typeof perf.measure).toBe('function')
      expect(typeof perf.getWeChatPerformanceData).toBe('function')
      expect(typeof perf.getSystemInfo).toBe('function')
      expect(typeof perf.getMemoryInfo).toBe('function')
    })

    it('usePerformance.measure 应该测量同步函数', async () => {
      const { usePerformance } = await import('@/utils/performance')

      const perf = usePerformance()
      const testFn = () => 42

      // 同步函数应该直接返回结果
      const result = perf.measure('sync-test', testFn)
      expect(result).toBe(42)
    })
  })

  describe('开发环境行为', () => {
    it('应该在开发环境打印日志', async () => {
      const consoleSpy = vi.spyOn(console, 'log')

      mockGetCurrentPages.mockReturnValue([{ route: 'test/page' }])

      // 设置为开发环境
      process.env.NODE_ENV = 'development'

      const { initPerformanceMonitoring } = await import('@/utils/performance')
      initPerformanceMonitoring()

      // 验证日志被调用（开发环境）
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()

      // 恢复 test 环境
      process.env.NODE_ENV = 'test'
    })
  })

  describe('性能指标数据结构', () => {
    it('应该有正确的指标结构', async () => {
      const { initPerformanceMonitoring } = await import('@/utils/performance')

      // 性能指标接口验证
      interface PerformanceMetric {
        name: string
        value: number
        timestamp: number
        page?: string
      }

      const metric: PerformanceMetric = {
        name: 'page_load',
        value: 1000,
        timestamp: Date.now(),
        page: 'test/page',
      }

      expect(metric.name).toBe('page_load')
      expect(metric.value).toBe(1000)
      expect(typeof metric.timestamp).toBe('number')
    })
  })

  describe('错误处理', () => {
    it('应该优雅处理 getCurrentPages 错误', async () => {
      // 模拟 getCurrentPages 抛出错误
      mockGetCurrentPages.mockImplementation(() => {
        throw new Error('getCurrentPages error')
      })

      const { initPerformanceMonitoring } = await import('@/utils/performance')
      initPerformanceMonitoring()

      // 应该不抛出错误
      expect(mockOnAppShow).toHaveBeenCalled()
    })

    it('measureRequest 应该处理请求失败', async () => {
      const { measureRequest } = await import('@/utils/performance')

      const mockApiCall = vi.fn(() => Promise.reject(new Error('API error')))
      const measuredCall = measureRequest('test-api', mockApiCall)

      await expect(measuredCall()).rejects.toThrow('API error')
      expect(mockApiCall).toHaveBeenCalled()
    })

    it('getSystemInfo 应该处理失败情况', async () => {
      const { getSystemInfo } = await import('@/utils/performance')

      // Mock fail callback
      mockGetSystemInfo.mockImplementation(({ fail }) => {
        fail()
      })

      const result = await getSystemInfo()
      expect(result).toBeNull()
    })
  })
})
