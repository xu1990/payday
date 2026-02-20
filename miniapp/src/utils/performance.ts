/**
 * 小程序性能监控工具
 * 使用 uni-app 和微信小程序性能 API
 *
 * 监控指标：
 * - 页面加载时间
 * - API 请求时间
 * - 渲染性能
 * - 内存使用
 */

// 性能指标接口
interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  page?: string
}

// 是否已经初始化
let isInitialized = false
let currentPage = ''

/**
 * 初始化性能监控
 * 应该在应用启动时调用一次
 */
export function initPerformanceMonitoring() {
  if (isInitialized) return
  if (typeof uni === 'undefined') return

  isInitialized = true

  // 监听页面显示事件
  uni.onAppShow(() => {
    // 小程序从后台进入前台
    reportPageView()
  })

  // 开发环境打印提示
  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance] Monitoring initialized')
  }
}

/**
 * 报告页面访问
 */
function reportPageView() {
  const pages = getCurrentPages()
  if (pages.length > 0) {
    currentPage = pages[pages.length - 1].route
    reportMetric({
      name: 'page_view',
      value: Date.now(),
      timestamp: Date.now(),
      page: currentPage,
    })
  }
}

/**
 * 获取当前页面栈
 */
function getCurrentPages(): any[] {
  // 使用 getCurrentPages 获取当前页面栈
  // 注意：这是 uni-app 的扩展 API
  try {
    return getCurrentPages ? getCurrentPages() : []
  } catch {
    return []
  }
}

/**
 * 上报性能指标
 */
function reportMetric(metric: PerformanceMetric) {
  // 开发环境打印到控制台
  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance]', metric.name, metric)
  }

  // 生产环境上报
  if (process.env.NODE_ENV === 'production') {
    // TODO: 上报到后端统计接口
    // 例如:
    // uni.request({
    //   url: '/api/v1/analytics/performance',
    //   method: 'POST',
    //   data: metric,
    // })
  }
}

/**
 * 测量 API 请求时间
 * 包装请求函数并自动记录执行时间
 */
export function measureRequest<T extends (...args: any[]) => any>(name: string, requestFn: T): T {
  return (...args: Parameters<T>) => {
    const start = Date.now()

    return requestFn(...args)
      .then(result => {
        const duration = Date.now() - start
        reportMetric({
          name: `api_request_${name}`,
          value: duration,
          timestamp: Date.now(),
          page: currentPage || 'unknown',
        })

        return result
      })
      .catch(error => {
        const duration = Date.now() - start
        reportMetric({
          name: `api_request_${name}_failed`,
          value: duration,
          timestamp: Date.now(),
          page: currentPage || 'unknown',
        })

        throw error
      })
  }
}

/**
 * 测量页面渲染时间
 * 在页面 onReady 之后调用
 */
export function measurePageRender(pageName: string) {
  if (typeof performance === 'undefined') {
    return
  }

  // 尝试使用 Performance API（如果可用）
  try {
    const perfData = performance.getEntries()
    const navigationEntry = perfData.find(
      entry => entry.entryType === 'navigation'
    ) as PerformanceEntry & { duration?: number }

    if (navigationEntry && navigationEntry.duration) {
      reportMetric({
        name: 'page_render',
        value: navigationEntry.duration,
        timestamp: Date.now(),
        page: pageName,
      })
    }
  } catch (e) {
    // Performance API 不可用，使用启动时间估算
    const app = getApp()
    if (app && app.onLaunch) {
      const launchTime = Date.now() - (app.globalData?.launchTime || Date.now())
      reportMetric({
        name: 'page_render_estimated',
        value: launchTime,
        timestamp: Date.now(),
        page: pageName,
      })
    }
  }
}

/**
 * 获取微信小程序性能数据
 * 仅在微信小程序中可用
 */
export function getWeChatPerformanceData() {
  // #ifndef MP-WEIXIN
  return null
  // #endif

  // #ifdef MP-WEIXIN
  try {
    if (typeof wx === 'undefined' || !wx.getPerformance) {
      return null
    }

    const performance = wx.getPerformance()
    return {
      // 网络请求统计
      network: performance.getEntries()?.filter((e: any) => e.entryType === 'request') || [],
      // 页面渲染统计
      rendering: performance.getEntries()?.filter((e: any) => e.entryType === 'render') || [],
      // 脚本执行统计
      script: performance.getEntries()?.filter((e: any) => e.entryType === 'script') || [],
    }
  } catch (e) {
    console.warn('[Performance] Failed to get WeChat performance data:', e)
    return null
  }
  // #endif
}

/**
 * 获取系统信息（用于性能分析）
 */
export function getSystemInfo() {
  return new Promise(resolve => {
    uni.getSystemInfo({
      success: res => {
        resolve({
          brand: res.brand,
          model: res.model,
          system: res.system,
          platform: res.platform,
          screenWidth: res.screenWidth,
          screenHeight: res.screenHeight,
          pixelRatio: res.pixelRatio,
          language: res.language,
          version: res.version,
          fontSizeSetting: res.fontSizeSetting,
        })
      },
      fail: () => {
        resolve(null)
      },
    })
  })
}

/**
 * 获取内存信息（仅微信小程序）
 */
export function getMemoryInfo() {
  // #ifndef MP-WEIXIN
  return Promise.resolve(null)
  // #endif

  // #ifdef MP-WEIXIN
  return new Promise(resolve => {
    if (typeof wx === 'undefined' || !wx.getPerformance) {
      resolve(null)
      return
    }

    wx.getPerformance({
      success: (res: any) => {
        if (res.memory) {
          resolve({
            used: res.memory.used,
            limit: res.memory.limit,
            percentage: (res.memory.used / res.memory.limit) * 100,
          })
        } else {
          resolve(null)
        }
      },
      fail: () => {
        resolve(null)
      },
    })
  })
  // #endif
}

/**
 * 监控 Composition API
 * 在组件中使用
 */
export function usePerformance() {
  const init = () => {
    initPerformanceMonitoring()
  }

  const measure = (name: string, fn: () => any) => {
    const start = Date.now()
    const result = fn()

    if (result && typeof result.then === 'function') {
      return result.then(() => {
        const duration = Date.now() - start
        reportMetric({
          name,
          value: duration,
          timestamp: Date.now(),
        })
      })
    } else {
      const duration = Date.now() - start
      reportMetric({
        name,
        value: duration,
        timestamp: Date.now(),
      })
      return result
    }
  }

  return {
    init,
    measure,
    getWeChatPerformanceData,
    getSystemInfo,
    getMemoryInfo,
  }
}
