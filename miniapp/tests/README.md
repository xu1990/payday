# Miniapp 测试指南

## 测试框架说明

本项目使用 **Vitest** 作为测试框架。由于 uni-app 小程序的特殊性，当前测试主要针对：

- ✅ **工具函数** (utils)
- ✅ **Composables** (组合式函数)
- ✅ **Pinia Stores** (状态管理)
- ⚠️ **页面和组件** (需要小程序环境，当前暂不支持)

## 为什么不完全支持小程序组件测试？

uni-app 小程序运行在特定的小程序环境中，包括：
- 微信小程序环境
- 支付宝小程序环境
- 其他平台环境

这些环境在普通 Node.js 或浏览器中无法完全模拟。因此，我们：

1. **优先测试纯逻辑**: 工具函数、composables、stores
2. **手动测试**: 页面和组件需要在小程序开发工具中手动测试
3. **未来改进**: 可能考虑使用 miniprogram-simulate 等工具

## 安装测试依赖

```bash
cd miniapp
npm install
```

新增的测试依赖：
- `vitest`: 测试运行器
- `@vitest/ui`: 可视化测试界面
- `@vitest/coverage-v8`: 代码覆盖率工具
- `happy-dom`: 轻量级 DOM 环境（比 jsdom 更快）
- `@vue/test-utils`: Vue 组件测试工具

## 运行测试

### 交互模式（推荐）

```bash
npm run test
```

启动 Vitest UI，可以在浏览器中查看测试结果。

### 命令行模式

```bash
# 运行所有测试一次
npm run test:run

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 测试结构

```
tests/
├── setup.ts              # 全局测试环境配置（mock uni-app 对象）
├── unit/
    └── utils/
        └── error.test.ts    # 工具函数测试
```

## 编写测试

### 示例：测试工具函数

```typescript
// tests/unit/utils/myUtil.test.ts
import { describe, it, expect } from 'vitest'
import { myFunction } from '@/utils/myUtil'

describe('myFunction', () => {
  it('should return correct result', () => {
    const result = myFunction('input')
    expect(result).toBe('expected')
  })
})
```

### 示例：测试 Composable

```typescript
// tests/unit/composables/useDebounce.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useDebounce } from '@/utils/useDebounce'

describe('useDebounce', () => {
  it('should debounce function calls', () => {
    vi.useFakeTimers()

    let callCount = 0
    const debouncedFn = useDebounce(() => {
      callCount++
    }, 300)

    debouncedFn()
    debouncedFn()

    expect(callCount).toBe(0)

    vi.advanceTimersByTime(300)
    expect(callCount).toBe(1)
  })
})
```

### Mock uni-app 全局对象

在 `tests/setup.ts` 中已经 mock 了常用的 uni-app API：

```typescript
global.uni = {
  navigateTo: vi.fn(),
  navigateBack: vi.fn(),
  getSystemInfoSync: vi.fn(),
  getStorageSync: vi.fn(() => ''),
  setStorageSync: vi.fn(),
  showToast: vi.fn(),
  // ... 其他 API
}
```

如果需要自定义 mock：

```typescript
import { vi } from 'vitest'

// Mock 特定 API
global.uni.getStorageSync = vi.fn(() => 'custom value')

// 测试
const result = uni.getStorageSync('key')
expect(result).toBe('custom value')
```

## 测试覆盖重点

### 高优先级（必须测试）

1. **工具函数**: 所有数据转换、验证、计算函数
2. **错误处理**: HTTP 错误映射、用户消息提取
3. **Composables**: 防抖、节流、请求取消等逻辑
4. **Pinia Stores**: 状态管理逻辑

### 中优先级（建议测试）

1. **API 客户端**: 请求格式化、错误处理
2. **常用逻辑**: 分页、过滤、排序

### 低优先级（手动测试）

1. **页面组件**: 需要在小程序开发工具中测试
2. **UI 组件**: LazyImage、Loading 等

## 覆盖率目标

- **工具函数**: > 90%
- **Composables**: > 85%
- **Stores**: > 80%
- **整体**: > 75%

## 常见问题

### Q: 为什么不测试 Vue 组件？

A: uni-app 小程序组件依赖特定的运行时环境。普通的 Vitest + happy-dom 无法完全模拟小程序环境。建议：

1. 优先测试纯逻辑代码
2. 使用微信开发者工具进行手动测试
3. 考虑使用真实的设备进行测试

### Q: 如何测试需要微信 API 的代码？

A: 在 `tests/setup.ts` 中已经 mock 了常用的 uni-app API。你可以：

```typescript
// 自定义 mock 返回值
global.uni.login = vi.fn(() => ({
  code: 'test_code',
}))

// 测试
const result = await uni.login()
expect(result.code).toBe('test_code')
```

### Q: 能否在 CI/CD 中运行测试？

A: 可以！由于我们不依赖小程序环境，普通的 CI 环境就可以运行：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: npm run test:run
```

## 参考资源

- [Vitest 官方文档](https://vitest.dev/)
- [Vue Test Utils 文档](https://test-utils.vuejs.org/)
- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [微信小程序测试指南](https://developers.weixin.qq.com/miniprogram/dev/framework/usibility-of-test/)
