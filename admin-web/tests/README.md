# Admin-Web 测试指南

## 测试框架

本项目使用 **Vitest** + **@vue/test-utils** 作为测试框架。

### 为什么选择 Vitest？

- ⚡️ 与 Vite 无缝集成，速度快
- 🎯 API 与 Jest 类似，学习成本低
- 🔧 原生支持 ESM 和 TypeScript
- 📊 内置代码覆盖率报告

## 安装依赖

首次运行测试前，需要安装测试依赖：

```bash
cd admin-web
npm install
```

这会安装以下测试相关的开发依赖：

- `@vue/test-utils`: Vue 组件测试工具
- `vitest`: 测试运行器
- `@vitest/ui`: 可视化测试界面
- `jsdom`: DOM 环境模拟
- `@vitest/coverage-v8`: 代码覆盖率工具

## 运行测试

### 交互模式（推荐开发时使用）

```bash
npm run test
```

启动 Vitest UI，可以在浏览器中查看测试结果和覆盖率。

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
├── setup.ts              # 全局测试环境配置
└── unit/
    └── components/
        ├── StatusTag.test.vue
        └── ActionButtons.test.vue
```

## 编写测试

### 示例：测试一个 Vue 组件

```vue
<!-- MyComponent.test.vue -->
<script setup lang="ts">
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('should render correctly', () => {
    const wrapper = mount(MyComponent, {
      props: {
        title: 'Hello',
      },
    })

    expect(wrapper.text()).toContain('Hello')
  })

  it('should emit click event', async () => {
    const wrapper = mount(MyComponent)

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
</script>
```

### 最佳实践

1. **测试文件命名**: 使用 `.test.vue` 或 `.spec.vue` 后缀
2. **测试描述**: 使用清晰的中文描述，说明测试目的
3. **测试分组**: 使用 `describe` 将相关测试分组
4. **隔离性**: 每个测试应该独立运行，不依赖其他测试
5. **可读性**: 测试代码应该像文档一样易读

### 覆盖率目标

- **语句覆盖率**: > 80%
- **分支覆盖率**: > 75%
- **函数覆盖率**: > 80%
- **行覆盖率**: > 80%

## 常见问题

### Q: 测试运行失败，提示找不到模块？

A: 确保已运行 `npm install` 安装所有依赖。

### Q: 如何测试需要 Pinia store 的组件？

A: 在 `tests/setup.ts` 中已经全局 mock 了 Pinia stores。如果需要自定义：

```ts
import { setActivePinia, createPinia } from 'pinia'
import { createApp } from 'vue'

const app = createApp({})
const pinia = createPinia()
app.use(pinia)
setActivePinia(pinia)
```

### Q: 如何测试 Vue Router？

A: 在 `tests/setup.ts` 中已经全局 mock 了 Vue Router。如需自定义：

```ts
import { Router } from 'vue-router'

const router = new Router({
  history: createMemoryHistory(),
  routes: [...],
})
```

## 参考资源

- [Vitest 官方文档](https://vitest.dev/)
- [@vue/test-utils 文档](https://test-utils.vuejs.org/)
- [Vue 3 测试指南](https://vuejs.org/guide/scaling-up/testing.html)
