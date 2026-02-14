# Admin-Web Storybook 文档

## 什么是 Storybook？

Storybook 是一个用于独立开发 UI 组件的开源工具。它使得组织和测试 UI 组件变得更容易。

## 为什么使用 Storybook？

1. **隔离开发**: 在独立环境中开发组件，不依赖应用路由或状态
2. **可视化测试**: 快速查看不同 props 和状态下的组件表现
3. **交互式文档**: 动态生成组件文档，提升开发体验
4. **回归测试**: 快速发现组件变更导致的问题
5. **团队协作**: 设计师和开发者可以在同一界面讨论组件

## 安装

```bash
cd admin-web
npm install
```

新增的依赖包括 Storybook 核心和 Vue 3 插件。

## 运行 Storybook

### 开发模式（热重载）

```bash
npm run storybook
```

启动后，访问 `http://localhost:6006`

### 构建静态版本

```bash
npm run build-storybook
```

构建输出到 `storybook-static` 目录。

## Story 文件结构

```
src/components/
├── StatusTag.stories.vue      # StatusTag 组件的 stories
├── ActionButtons.stories.vue    # ActionButtons 组件的 stories
└── BaseDataTable.stories.vue  # BaseDataTable 组件的 stories
```

## 编写 Stories

### 基础结构

```vue
<script setup lang="ts">
import type { Meta, StoryObj } from '@storybook/vue3'
import MyComponent from './MyComponent.vue'

// 定义 Story 元数据
const meta: Meta = {
  title: 'Components/MyComponent',  // 组件在侧边栏的路径
  component: MyComponent,
  tags: ['autodocs'],  // 自动生成文档
  argTypes: { /* props 类型定义 */ },
}

export default meta

// 定义 Story
const Template: StoryObj = {
  render: (args) => ({
    components: { MyComponent },
    template: '<MyComponent v-bind="args" />',
  }),
}

export const Default = {
  ...Template,
  args: {
    // 默认 props
  },
}
</script>
```

### 命名约定

1. **导出 Default story**: 展示组件最常用的状态
2. **描述性命名**: 使用 `Loading`, `Empty`, `Error` 等清晰命名
3. **All variants**: 创建 `All...` story 展示所有变体

### 示例：StatusTag Stories

```vue
export const Active = {
  ...Template,
  args: { status: 'active' },
  parameters: {
    docs: {
      description: { story: '激活状态 - 显示为绿色成功标签' },
    },
  },
}

export const Disabled = {
  ...Template,
  args: { status: 'disabled' },
}
```

## 组件文档

### Meta 配置

```typescript
const meta: Meta = {
  title: 'Category/ComponentName',  // 侧边栏路径
  component: MyComponent,             // 组件引用
  tags: ['autodocs'],                // 自动文档生成
  argTypes: { /* props */ },          // Props 类型定义
}
```

### 参数描述

```typescript
argTypes: {
  propName: {
    description: '属性描述',           // 属性说明
    control: 'select',                  // 控制类型：select, boolean, text, number...
    options: ['option1', 'option2'],   // 可选值（select 类型）
    table: {                            // 额外表格信息
      category: 'Advanced',
      defaultValue: 'default value',
    },
  },
}
```

### Story 级别

使用 `parameters` 添加额外配置：

```typescript
export const MyStory = {
  ...Template,
  args: { /* ... */ },
  parameters: {
    docs: {
      description: {
        story: 'Story 的详细描述',
      },
    },
    backgrounds: {
      // 覆盖默认背景
      default: 'dark',
    },
  },
}
```

## 装饰器 (Decorators)

在 `.storybook/preview.ts` 中配置的全局装饰器：

### 1. Router Mock

```typescript
decorators: [
  (story, context) => {
    const mockRouter = {
      push: () => {},
      replace: () => {},
      go: () => {},
      // ...
    }
    ;(context as any).router = mockRouter
    return story()
  },
]
```

### 2. Pinia Store Mock

```typescript
decorators: [
  (story, context) => {
    const mockStore = { /* store data */ }
    ;(context as any).store = mockStore
    return story()
  },
]
```

### 3. 主题装饰器

```typescript
import { withThemeByDataAttribute } from '@storybook/addon-themes'

decorators: [
  withThemeByDataAttribute({
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
    defaultTheme: 'light',
  }),
]
```

## 最佳实践

### 1. Props 设计

- ✅ 提供合理的默认值
- ✅ 使用 TypeScript 定义类型
- ✅ 为每个 prop 提供清晰的描述

### 2. Stories 组织

- ✅ 按功能分组相关 stories
- ✅ 从简单到复杂排列
- ✅ 包含边界情况（empty, error, loading）

### 3. 可访问性

- ✅ 确保所有交互元素有 ARIA 标签
- ✅ 测试键盘导航
- ✅ 检查颜色对比度

### 4. 文档质量

- ✅ 描述组件用途，不只是实现细节
- ✅ 提供使用示例
- ✅ 说明 props 和 events

## 当前组件 Stories

### StatusTag (状态标签)

Stories:
- `Active` - 激活状态
- `Enabled` - 启用状态
- `Pending` - 待处理
- `Disabled` - 禁用
- `Rejected` - 已拒绝
- `Unknown` - 未知状态
- `AllStatuses` - 所有状态展示

**功能**: 显示不同状态的可复用标签组件

---

### ActionButtons (操作按钮组)

Stories:
- `Default` - 默认配置
- `AllButtonsVisible` - 所有按钮可见
- `OnlyEditAndDelete` - 仅编辑和删除
- `OnlyDelete` - 仅删除（危险操作）
- `WithCustomSlot` - 自定义插槽

**功能**: 标准化的操作按钮组，支持编辑、切换、删除

---

### BaseDataTable (数据表格)

Stories:
- `Default` - 正常数据展示
- `Loading` - 加载状态
- `Empty` - 空数据状态
- `WithPagination` - 带分页

**功能**: 带分页、加载、空状态的数据表格

## 集成到 CI/CD

### GitHub Actions 示例

```yaml
name: Build Storybook

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci
        working-directory: ./admin-web

      - name: Build Storybook
        run: npm run build-storybook
        working-directory: ./admin-web

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./admin-web/storybook-static
```

## 参考资源

- [Storybook 官方文档](https://storybook.vuejs.org/)
- [Storybook for Vue 3](https://github.com/storybookjs/vue3)
- [添加文档](https://storybook.js.org/docs/vue/writing-docs/introduction)
