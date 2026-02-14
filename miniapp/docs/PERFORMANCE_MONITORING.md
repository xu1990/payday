# 前端性能监控指南

## Admin-Web (Web 应用)

### 概述

Admin-Web 使用 **web-vitals** 库收集 Core Web Vitals 指标，这是 Google 推荐的 Web 性能标准。

### 监控指标

| 指标 | 描述 | 良好 | 需改进 | 较差 |
|------|------|------|---------|------|
| **LCP** | 最大内容绘制 | < 2.5s | < 4s | > 4s |
| **FID** | 首次输入延迟 | < 100ms | < 300ms | > 300ms |
| **CLS** | 累积布局偏移 | < 0.1 | < 0.25 | > 0.25 |
| **FCP** | 首次内容绘制 | < 1.8s | < 3s | > 3s |

### 自动初始化

性能监控在 `src/main.ts` 中自动初始化：

```typescript
import { initPerformanceMonitoring } from './utils/performance'

// 应用启动时立即初始化
initPerformanceMonitoring()
```

### 手动使用

#### 测量自定义操作

```typescript
import { reportCustomTiming } from '@/utils/performance'

// 测量某个操作的执行时间
const start = performance.now()
// ... 执行操作 ...
const duration = performance.now() - start
reportCustomTiming('custom_operation', duration)
```

#### 包装异步函数

```typescript
import { measurePerformance } from '@/utils/performance'

const fetchData = measurePerformance('fetch_data', async () => {
  const response = await api.get('/data')
  return response.data
})

// 自动上报执行时间
```

#### 获取性能数据

```typescript
import { getPerformanceData } from '@/utils/performance'

const perfData = getPerformanceData()
console.log('Page Load Time:', perfData.domContentLoaded)
console.log('DNS Lookup:', perfData.dnsLookup)
```

### 安装依赖

```bash
cd admin-web
npm install
```

这会安装 `web-vitals` 依赖。

---

## Miniapp (小程序)

### 概述

小程序使用自定义的性能监控工具，基于：
- uni-app 性能 API
- 微信小程序 `wx.getPerformance()`
- 自定义时间测量

### 监控指标

| 指标 | 描述 | 用途 |
|------|------|------|
| **页面访问** | 记录页面切换 | 分析用户路径 |
| **API 请求** | 测量请求时间 | 识别慢接口 |
| **页面渲染** | 测量加载时间 | 优化首屏 |
| **内存使用** | 监控内存占用 | 防止内存泄漏 |
| **系统信息** | 设备和平台信息 | 分段性能数据 |

### 基础使用

#### 初始化监控

```typescript
import { initPerformanceMonitoring } from '@/utils/performance'

initPerformanceMonitoring()
```

#### 测量 API 请求

```typescript
import { measureRequest } from '@/utils/performance'

const apiRequest = measureRequest('get_user_info', () => {
  return uni.request({
    url: '/api/v1/users/info',
    method: 'GET',
  })
})

// 自动上报请求时间
```

#### 测量页面渲染

```typescript
import { measurePageRender } from '@/utils/performance'

export default {
  onReady() {
    measurePageRender('index')
  },
}
```

#### 获取性能数据

```typescript
import { getWeChatPerformanceData, getSystemInfo, getMemoryInfo } from '@/utils/performance'

// 微信小程序性能数据（仅微信）
const perfData = await getWeChatPerformanceData()

// 系统信息
const systemInfo = await getSystemInfo()

// 内存信息（仅微信）
const memoryInfo = await getMemoryInfo()
```

### 在组件中使用

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { usePerformance } from '@/utils/performance'

const { init, measure } = usePerformance()

onMounted(() => {
  init()

  // 测量某个操作
  measure('load_data', () => {
    return fetchData()
  })
})
</script>
```

---

## 数据上报

### 当前状态

⚠️ **当前仅开发环境输出到控制台，生产环境需要配置上报目标。**

### 配置上报

#### Admin-Web

编辑 `src/utils/performance.ts`:

```typescript
function reportMetric(metric: VitalMetric) {
  // 开发环境
  if (import.meta.env.DEV) {
    console.log('[Performance]', metric.name, metric)
  }

  // 生产环境 - 上报到 Sentry
  if (!import.meta.env.DEV) {
    import('@sentry/vue').then(({ captureMessage }) => {
      captureMessage('Performance Metric', {
        level: metric.rating === 'poor' ? 'warning' : 'info',
        extra: metric,
      })
    })
  }

  // 或上报到自己的统计端点
  // fetch('/api/v1/analytics/performance', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(metric),
  // })
}
```

#### Miniapp

编辑 `src/utils/performance.ts`:

```typescript
function reportMetric(metric: PerformanceMetric) {
  // 开发环境
  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance]', metric.name, metric)
  }

  // 生产环境 - 上报到后端
  if (process.env.NODE_ENV === 'production') {
    uni.request({
      url: '/api/v1/analytics/performance',
      method: 'POST',
      data: metric,
    })
  }
}
```

---

## 性能优化建议

### Admin-Web 优化

1. **LCP 优化**:
   - 预加载关键资源
   - 优化图片大小和格式
   - 使用 CDN 加速

2. **FID 优化**:
   - 减少 JavaScript 执行时间
   - 拆分长任务
   - 使用 Web Workers

3. **CLS 优化**:
   - 为图片和视频预留空间
   - 避免动态插入内容
   - 使用 CSS transform 动画

### Miniapp 优化

1. **减少包体积**:
   - 按需加载
   - 分包加载
   - 移除未使用的资源

2. **渲染性能**:
   - 避免频繁 setData
   - 使用虚拟列表
   - 优化图片加载

3. **网络优化**:
   - 使用缓存
   - 合并请求
   - 压缩数据

---

## 参考资源

- [Web Vitals](https://web.dev/vitals/)
- [web-vitals 库](https://github.com/GoogleChrome/web-vitals)
- [uni-app 性能优化](https://uniapp.dcloud.net.cn/tutorial/performance.html)
- [微信小程序性能分析](https://developers.weixin.qq.com/miniprogram/dev/framework/usability-of-test/)

---

## TODO

- [ ] 配置生产环境上报目标（Sentry 或自定义端点）
- [ ] 添加性能告警机制
- [ ] 建立性能基线和目标
- [ ] 定期审查性能数据并优化
