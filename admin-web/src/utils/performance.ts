/**
 * 前端性能监控工具
 * 使用 web-vitals 库收集 Core Web Vitals 指标
 *
 * 监控指标：
 * - LCP (Largest Contentful Paint): 最大内容绘制
 * - FID (First Input Delay): 首次输入延迟
 * - CLS (Cumulative Layout Shift): 累积布局偏移
 *
 * 参考: https://web.dev/vitals/
 */

import { onCLS, onFID, onLCP, onFCP } from 'web-vitals'

// 性能指标接口
interface VitalMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  timestamp: number
}

// 评分阈值（基于 Web 标准）
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 }, // 毫秒
  FID: { good: 100, poor: 300 }, // 毫秒
  CLS: { good: 0.1, poor: 0.25 }, // 分数
  FCP: { good: 1800, poor: 3000 }, // 毫秒
}

// 评分函数
function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS]
  if (!threshold) return 'needs-improvement'

  if (value <= threshold.good) return 'good'
  if (value <= threshold.poor) return 'needs-improvement'
  return 'poor'
}

// 上报性能指标
function reportMetric(metric: VitalMetric) {
  // 开发环境打印到控制台
  if (import.meta.env.DEV) {
    console.log('[Performance]', metric.name, metric)
  }

  // 生产环境上报到监控系统
  if (!import.meta.env.DEV) {
    // TODO: 上报到 Sentry 或其他监控平台
    // 例如:
    // Sentry.captureMessage('Performance Metric', {
    //   level: metric.rating === 'poor' ? 'warning' : 'info',
    //   extra: metric,
    // })

    // 或发送到自己的统计端点
    // fetch('/api/v1/analytics/performance', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(metric),
    // })
  }
}

// 是否已经初始化
let isInitialized = false

/**
 * 初始化性能监控
 * 应该在应用启动时调用一次
 */
export function initPerformanceMonitoring() {
  if (isInitialized) return
  if (typeof window === 'undefined') return

  isInitialized = true

  // LCP (Largest Contentful Paint)
  onLCP((metric) => {
    reportMetric({
      name: 'LCP',
      value: metric.value,
      rating: getRating('LCP', metric.value),
      timestamp: Date.now(),
    })
  })

  // FID (First Input Delay)
  onFID((metric) => {
    reportMetric({
      name: 'FID',
      value: metric.value,
      rating: getRating('FID', metric.value),
      timestamp: Date.now(),
    })
  })

  // CLS (Cumulative Layout Shift)
  onCLS((metric) => {
    reportMetric({
      name: 'CLS',
      value: metric.value,
      rating: getRating('CLS', metric.value),
      timestamp: Date.now(),
    })
  })

  // FCP (First Contentful Paint) - 额外的有用的指标
  onFCP((metric) => {
    reportMetric({
      name: 'FCP',
      value: metric.value,
      rating: getRating('FCP', metric.value),
      timestamp: Date.now(),
    })
  })
}

/**
 * 手动报告自定义性能指标
 * 用于监控特定操作的性能
 */
export function reportCustomTiming(name: string, duration: number) {
  const metric: VitalMetric = {
    name,
    value: duration,
    rating: duration < 1000 ? 'good' : duration < 3000 ? 'needs-improvement' : 'poor',
    timestamp: Date.now(),
  }

  reportMetric(metric)
}

/**
 * 测量异步操作性能
 * 包装异步函数并自动报告其执行时间
 */
export function measurePerformance<T extends (...args: any[]) => any>(
  name: string,
  fn: T
): T {
  return (...args: Parameters<T>) => {
    const start = performance.now()

    return fn(...args).finally(() => {
      const duration = performance.now() - start
      reportCustomTiming(name, duration)
    })
  }
}

/**
 * 获取当前页面性能数据
 * 用于调试和分析
 */
export function getPerformanceData() {
  if (typeof window === 'undefined') return null

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming

  if (!navigation) return null

  return {
    // 页面加载时间
    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
    loadComplete: navigation.loadEventEnd - navigation.fetchStart,
    // DNS 查询时间
    dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
    // 服务器响应时间
    serverResponse: navigation.responseEnd - navigation.requestStart,
    // 页面渲染时间
    pageRender: navigation.domComplete - navigation.domInteractive,
    // 其他有用的指标
    redirectCount: performance.getEntriesByType('navigation').length - 1,
    resourceCount: performance.getEntriesByType('resource').length,
  }
}

/**
 * 性能监控 Composition API
 * 在组件中使用
 */
export function usePerformance() {
  const init = () => {
    if (typeof window !== 'undefined') {
      initPerformanceMonitoring()
    }
  }

  // 组件挂载时初始化
  onMounted(init)

  return {
    init,
    reportCustomTiming,
    getPerformanceData,
  }
}
