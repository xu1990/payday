# Miniapp 设计系统重构方案

## 概述

基于 `ui.md` 智能液态界面设计规范，为薪日 PayDay 小程序创建完整的设计系统，包含：
- SCSS 变量系统
- 玻璃效果（Glass Morphism）
- 暗黑模式支持
- 动态色彩效果
- Vue 组件库

## 设计目标

- **全面重构** - 替换所有现有页面样式
- **完整玻璃效果** - 背景模糊 + 透明度
- **暗黑模式** - 跟随系统切换
- **动态色彩** - AI 呼吸效果、情绪映射

---

## 1. 目录结构

```
miniapp/src/
├── styles/
│   ├── tokens/
│   │   ├── _colors.scss        # 色彩变量（品牌色、语义色、中性色）
│   │   ├── _typography.scss    # 字体排版
│   │   ├── _spacing.scss       # 间距系统
│   │   ├── _shadows.scss       # 阴影与玻璃效果
│   │   ├── _animations.scss    # 动态效果（呼吸、渐变）
│   │   └── _index.scss         # Token 汇总导出
│   ├── themes/
│   │   ├── _light.scss         # 浅色主题变量覆盖
│   │   ├── _dark.scss          # 暗黑主题变量覆盖
│   │   └── _index.scss         # 主题切换逻辑
│   ├── _glass.scss             # 玻璃效果 mixins
│   ├── _utilities.scss         # 工具类
│   └── index.scss              # 全局样式入口
├── components/
│   ├── ui/                     # 基础 UI 组件
│   │   ├── PdButton.vue
│   │   ├── PdCard.vue
│   │   ├── PdInput.vue
│   │   ├── PdBadge.vue
│   │   ├── PdAvatar.vue
│   │   ├── PdNavBar.vue
│   │   ├── PdEmpty.vue
│   │   ├── PdLoading.vue
│   │   └── index.ts
│   └── ...
```

---

## 2. 色彩系统

### 2.1 品牌核心色

```scss
// tokens/_colors.scss

// 品牌色
$brand-primary: #4A6CF7;           // 主色 - 品牌主色、默认按钮、选中状态
$brand-secondary: #9D7BFF;         // 辅色 - 强调色、图标渐变起点、链接
$brand-primary-strong: #2A4AF0;    // 悬停状态、深色背景下的品牌色

// 渐变
$gradient-brand: linear-gradient(135deg, $brand-primary 0%, $brand-secondary 100%);
$gradient-ai-core: linear-gradient(135deg, #4A6CF7 0%, #9D7BFF 50%, #FFB443 100%);
```

### 2.2 语义色

```scss
// 语义色 - 所有颜色需满足 WCAG 2.2 无障碍标准
$semantic-success: #00C48C;   // 成功 - AAA (7:1)
$semantic-error: #FF5C5C;     // 错误 - AAA (7:1)
$semantic-warning: #FFB443;   // 警告 - AA (4.5:1)
$semantic-info: #54A0FF;      // 信息 - AA (4.5:1)
```

### 2.3 液态玻璃中性色（浅色模式）

```scss
// 背景层
$bg-base: #FFFFFF;
$bg-glass-subtle: rgba(0, 0, 0, 0.02);           // 极隐晦的底纹
$bg-glass-standard: rgba(255, 255, 255, 0.4);    // 标准卡片
$bg-glass-prominent: rgba(255, 255, 255, 0.7);   // 导航栏

// 文字层级（使用透明度区分）
$text-primary: rgba(0, 0, 0, 0.9);       // 标题、正文
$text-secondary: rgba(0, 0, 0, 0.6);     // 辅助信息
$text-tertiary: rgba(0, 0, 0, 0.35);     // 占位符、禁用状态
$text-disabled: rgba(0, 0, 0, 0.12);     // 完全禁用

// 边框
$border-subtle: rgba(0, 0, 0, 0.1);      // 分割线
$border-regular: rgba(0, 0, 0, 0.2);     // 卡片描边
$border-glow: rgba(255, 255, 255, 0.5);  // 玻璃边缘高光
```

### 2.4 暗黑模式

```scss
// themes/_dark.scss

// 背景层
$bg-base: #0A0C14;
$bg-glass-subtle: rgba(255, 255, 255, 0.02);
$bg-glass-standard: rgba(20, 25, 40, 0.7);
$bg-glass-prominent: rgba(10, 15, 30, 0.85);

// 文字层级
$text-primary: rgba(255, 255, 255, 0.92);
$text-secondary: rgba(255, 255, 255, 0.65);
$text-tertiary: rgba(255, 255, 255, 0.4);
$text-disabled: rgba(255, 255, 255, 0.15);

// 边框
$border-subtle: rgba(255, 255, 255, 0.08);
$border-regular: rgba(255, 255, 255, 0.15);
$border-glow: rgba(255, 255, 255, 0.1);

// 品牌色在暗黑模式下明度提升 5%
$brand-primary: lighten(#4A6CF7, 5%);
$brand-secondary: lighten(#9D7BFF, 5%);
```

### 2.5 动态功能色

```scss
// AI & 渐变强调色
$accent-cyan: #00C4CC;     // 数据流动画、连接状态
$accent-gold: #FFD966;     // 新功能引导、会员权益、高亮标记
```

---

## 3. 玻璃效果

### 3.1 核心 Mixins

```scss
// _glass.scss

// 标准玻璃卡片
@mixin glass-card($prominent: false) {
  background: if($prominent, var(--bg-glass-prominent), var(--bg-glass-standard));
  backdrop-filter: blur(20rpx);
  -webkit-backdrop-filter: blur(20rpx);
  border: 1rpx solid var(--border-regular);
  border-top-color: var(--border-glow);  // 顶部高光
  border-radius: 16rpx;
}

// 玻璃导航栏
@mixin glass-nav {
  background: var(--bg-glass-prominent);
  backdrop-filter: blur(30rpx);
  -webkit-backdrop-filter: blur(30rpx);
  border-bottom: 1rpx solid var(--border-subtle);
}

// 语义色玻璃适配
// 当语义色放置在毛玻璃效果之上时，添加 5% 白色叠加层
@mixin semantic-glass($color) {
  background: $color;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.05);
    border-radius: inherit;
    pointer-events: none;
  }
}
```

---

## 4. 动态效果

### 4.1 AI 呼吸效果

```scss
// _animations.scss

// AI 呼吸效果 - 3s 周期色相偏移
@keyframes breathe {
  0%, 100% { filter: hue-rotate(0deg); }
  50% { filter: hue-rotate(15deg); }
}

.ai-breathing {
  animation: breathe 3s ease-in-out infinite;
}
```

### 4.2 流光效果

```scss
// 流光效果 - 渐变位置动画
@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

.ai-shimmer {
  background: $gradient-ai-core;
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}
```

### 4.3 情绪映射

```scss
// 情绪映射 - 用户情绪低落时提升饱和度
.mood-warm {
  --accent-gold-saturation: 100%;
}

.mood-comfort {
  --accent-gold-saturation: 110%;
}
```

### 4.4 交互反馈

```scss
// 按压反馈
@keyframes press {
  0% { transform: scale(1); }
  50% { transform: scale(0.97); }
  100% { transform: scale(1); }
}

.btn-press:active {
  animation: press 0.15s ease-out;
}
```

---

## 5. 主题切换

```scss
// themes/_index.scss

:root {
  // 默认浅色主题
  --bg-base: #{$bg-base};
  --bg-glass-subtle: #{$bg-glass-subtle};
  --bg-glass-standard: #{$bg-glass-standard};
  --bg-glass-prominent: #{$bg-glass-prominent};
  --text-primary: #{$text-primary};
  --text-secondary: #{$text-secondary};
  --text-tertiary: #{$text-tertiary};
  --border-subtle: #{$border-subtle};
  --border-regular: #{$border-regular};
  --border-glow: #{$border-glow};
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-base: #{$bg-base-dark};
    --bg-glass-subtle: #{$bg-glass-subtle-dark};
    --bg-glass-standard: #{$bg-glass-standard-dark};
    --bg-glass-prominent: #{$bg-glass-prominent-dark};
    --text-primary: #{$text-primary-dark};
    --text-secondary: #{$text-secondary-dark};
    --text-tertiary: #{$text-tertiary-dark};
    --border-subtle: #{$border-subtle-dark};
    --border-regular: #{$border-regular-dark};
    --border-glow: #{$border-glow-dark};
  }
}

// 强制主题类（用于手动切换）
.theme-light {
  // 浅色主题变量
}

.theme-dark {
  // 暗黑主题变量
}
```

---

## 6. 组件库

### 6.1 组件清单

| 组件 | 说明 | 主要特性 |
|------|------|----------|
| `PdButton` | 按钮 | Primary/Outline/Link/Glass 变体，按压动画 |
| `PdCard` | 卡片 | 玻璃背景，顶部高光，可配置层级 |
| `PdInput` | 输入框 | 玻璃边框，聚焦状态，验证状态 |
| `PdBadge` | 徽标 | 语义色，玻璃适配 |
| `PdAvatar` | 头像 | 玻璃边框，尺寸变体 |
| `PdNavBar` | 导航栏 | 玻璃效果，暗黑适配 |
| `PdEmpty` | 空状态 | 图标 + 文案 |
| `PdLoading` | 加载 | AI 呼吸效果 |

### 6.2 PdButton

```vue
<!-- components/ui/PdButton.vue -->
<template>
  <button
    :class="['pd-btn', `pd-btn--${variant}`, { 'pd-btn--glass': glass }]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'outline' | 'link' | 'glass'
  glass?: boolean
  disabled?: boolean
}>()
</script>

<style lang="scss">
.pd-btn {
  padding: 20rpx 40rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  transition: all 0.2s;
  border: none;

  &--primary {
    background: $gradient-brand;
    color: #fff;
  }

  &--secondary {
    background: $brand-secondary;
    color: #fff;
  }

  &--outline {
    background: transparent;
    color: $brand-primary;
    border: 1rpx solid $brand-primary;
  }

  &--link {
    background: transparent;
    color: $brand-primary;
    padding: 0;
  }

  &--glass {
    @include glass-card();
    backdrop-filter: blur(10rpx);
    color: var(--text-primary);
  }

  &:active {
    transform: scale(0.97);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
```

### 6.3 PdCard

```vue
<!-- components/ui/PdCard.vue -->
<template>
  <view :class="['pd-card', `pd-card--${level}`]">
    <slot />
  </view>
</template>

<script setup lang="ts">
defineProps<{
  level?: 'subtle' | 'standard' | 'prominent'
}>()
</script>

<style lang="scss">
.pd-card {
  @include glass-card();
  padding: 24rpx;

  &--prominent {
    @include glass-card($prominent: true);
  }

  &--subtle {
    background: var(--bg-glass-subtle);
    backdrop-filter: none;
    border: none;
  }
}
</style>
```

---

## 7. 页面迁移计划

### 7.1 迁移优先级

**Phase 1 - 核心页面**
1. `index.vue` - 首页
2. `profile/index.vue` - 个人中心
3. `login/index.vue` - 登录页

**Phase 2 - 功能页面**
1. `point-mall/` - 积分商城模块
2. `salary-record/index.vue` - 工资记录
3. `feed/index.vue` - 动态流
4. `square/index.vue` - 广场

**Phase 3 - 次要页面**
- 设置、通知、主题选择等

### 7.2 迁移步骤

每个页面的迁移步骤：

1. **替换样式变量**
   - 硬编码颜色 → SCSS 变量
   - 例：`#07c160` → `$semantic-success`
   - 例：`#667eea` → `$brand-primary`

2. **应用玻璃效果**
   - 卡片 → `<PdCard>`
   - 按钮 → `<PdButton>`

3. **添加暗黑模式支持**
   - 检查 `var(--*)` CSS 变量使用
   - 测试暗黑模式显示

4. **添加动态效果**
   - AI 相关区域添加 `.ai-breathing`
   - 按钮添加按压反馈

### 7.3 示例：首页迁移

**迁移前**：
```scss
.user-bar {
  background: #fff;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.btn-primary {
  background: #07c160;
  color: #fff;
}

.mood-item.active {
  border-color: #07c160;
  background: #e8f8f0;
}
```

**迁移后**：
```scss
.user-bar {
  @include glass-card();
}

.btn-primary {
  @extend .pd-btn;
  @extend .pd-btn--primary;
}

.mood-item.active {
  border-color: $brand-primary;
  background: rgba($brand-primary, 0.1);
}
```

---

## 8. 无障碍标准

### 8.1 对比度要求

- 正文（<18pt）：对比度 ≥ 4.5:1
- 大文本（>18pt 粗体 或 >24pt）：对比度 ≥ 3:1
- UI 组件（图标、描边）：对比度 ≥ 3:1

### 8.2 高对比度模式

当用户开启系统高对比度模式时：
- 所有 rgba() 透明度颜色转换为最接近的纯色（HEX）
- 文字颜色变为纯黑 (#000000) 或纯白 (#FFFFFF)
- 品牌色保持不变，但需确保与背景对比度 ≥ 7:1

---

## 9. 技术决策

| 决策点 | 选择 | 原因 |
|--------|------|------|
| 样式预处理器 | SCSS | uni-app 默认支持，编译时优化 |
| 主题切换 | CSS 变量 | 运行时动态切换，支持暗黑模式 |
| 组件封装 | Vue SFC | 与现有架构一致，易于维护 |
| 玻璃效果 | backdrop-filter | 微信小程序支持良好 |

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| backdrop-filter 性能 | 低端设备卡顿 | 提供降级方案，检测性能后降级为纯色 |
| 暗黑模式测试覆盖 | 部分页面遗漏 | 建立暗黑模式测试清单 |
| 迁移工作量大 | 时间延期 | 分 Phase 进行，优先核心页面 |

---

## 附录：Token 命名规范

```scss
/* 类别-用途-状态-场景 */
:root {
  /* 品牌色 */
  --brand-primary-default: #4A6CF7;
  --brand-primary-hover: #2A4AF0;

  /* 背景色 */
  --background-glass-card: rgba(255,255,255,0.4);
  --background-glass-nav: rgba(255,255,255,0.7);

  /* 文字色 */
  --text-primary-light: rgba(0,0,0,0.9);
  --text-primary-dark: rgba(255,255,255,0.92);

  /* 语义色 - 深色模式变量 */
  --semantic-success-dark: #00BFA5;
}
```
