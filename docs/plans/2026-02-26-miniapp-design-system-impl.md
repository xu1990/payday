# Miniapp 设计系统实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为薪日 PayDay 小程序实现完整的设计系统，包含 SCSS 变量、玻璃效果、暗黑模式和 Vue 组件库。

**Architecture:** 采用 SCSS 变量 + CSS 变量混合方案，编译时优化性能，运行时支持主题切换。组件库封装为 Vue SFC，与现有架构一致。

**Tech Stack:** Vue 3, SCSS, uni-app, CSS Variables, backdrop-filter

---

## Task 1: 创建样式目录结构

**Files:**
- Create: `miniapp/src/styles/tokens/` (directory)
- Create: `miniapp/src/styles/themes/` (directory)

**Step 1: 创建目录结构**

Run:
```bash
mkdir -p miniapp/src/styles/tokens miniapp/src/styles/themes
```

Expected: 目录创建成功

**Step 2: 验证目录结构**

Run:
```bash
ls -la miniapp/src/styles/
```

Expected:
```
drwxr-xr-x   tokens/
drwxr-xr-x   themes/
```

**Step 3: Commit**

```bash
git add miniapp/src/styles/
git commit -m "chore(miniapp): create design system directory structure"
```

---

## Task 2: 创建色彩 Token 文件

**Files:**
- Create: `miniapp/src/styles/tokens/_colors.scss`

**Step 1: 创建色彩变量文件**

```scss
// miniapp/src/styles/tokens/_colors.scss
// 智能液态界面设计系统 - 色彩规范 v2.0.6

// ========================================
// 品牌核心色 (Primary Palette)
// ========================================

// 主色 - 品牌主色、默认按钮、选中状态
$brand-primary: #4A6CF7;

// 辅色 - 强调色、图标渐变起点、链接
$brand-secondary: #9D7BFF;

// 悬停状态、深色背景下的品牌色
$brand-primary-strong: #2A4AF0;

// ========================================
// 渐变
// ========================================

$gradient-brand: linear-gradient(135deg, $brand-primary 0%, $brand-secondary 100%);
$gradient-ai-core: linear-gradient(135deg, #4A6CF7 0%, #9D7BFF 50%, #FFB443 100%);

// ========================================
// 语义色 (Feedback & Status)
// 所有颜色满足 WCAG 2.2 无障碍标准
// ========================================

$semantic-success: #00C48C;   // 成功 - AAA (7:1)
$semantic-error: #FF5C5C;     // 错误 - AAA (7:1)
$semantic-warning: #FFB443;   // 警告 - AA (4.5:1)
$semantic-info: #54A0FF;      // 信息 - AA (4.5:1)

// ========================================
// 动态功能色 (AI & Gradient Accents)
// ========================================

$accent-cyan: #00C4CC;        // 数据流动画、连接状态
$accent-gold: #FFD966;        // 新功能引导、会员权益、高亮标记

// ========================================
// 液态玻璃中性色 - 浅色模式
// ========================================

// 背景层 (Background Layers)
$bg-base: #FFFFFF;
$bg-glass-subtle: rgba(0, 0, 0, 0.02);
$bg-glass-standard: rgba(255, 255, 255, 0.4);
$bg-glass-prominent: rgba(255, 255, 255, 0.7);

// 文字层级 (Text Hierarchy) - 使用透明度区分
$text-primary: rgba(0, 0, 0, 0.9);
$text-secondary: rgba(0, 0, 0, 0.6);
$text-tertiary: rgba(0, 0, 0, 0.35);
$text-disabled: rgba(0, 0, 0, 0.12);

// 边框与分割 (Borders & Strokes)
$border-subtle: rgba(0, 0, 0, 0.1);
$border-regular: rgba(0, 0, 0, 0.2);
$border-glow: rgba(255, 255, 255, 0.5);

// ========================================
// 液态玻璃中性色 - 暗黑模式
// ========================================

// 背景层
$bg-base-dark: #0A0C14;
$bg-glass-subtle-dark: rgba(255, 255, 255, 0.02);
$bg-glass-standard-dark: rgba(20, 25, 40, 0.7);
$bg-glass-prominent-dark: rgba(10, 15, 30, 0.85);

// 文字层级
$text-primary-dark: rgba(255, 255, 255, 0.92);
$text-secondary-dark: rgba(255, 255, 255, 0.65);
$text-tertiary-dark: rgba(255, 255, 255, 0.4);
$text-disabled-dark: rgba(255, 255, 255, 0.15);

// 边框
$border-subtle-dark: rgba(255, 255, 255, 0.08);
$border-regular-dark: rgba(255, 255, 255, 0.15);
$border-glow-dark: rgba(255, 255, 255, 0.1);

// 品牌色在暗黑模式下明度提升 5%
$brand-primary-dark: #5E7EF8;
$brand-secondary-dark: #AD8FFF;
```

**Step 2: 验证文件创建**

Run:
```bash
head -20 miniapp/src/styles/tokens/_colors.scss
```

Expected: 文件内容正确显示

**Step 3: Commit**

```bash
git add miniapp/src/styles/tokens/_colors.scss
git commit -m "feat(miniapp): add color tokens for design system"
```

---

## Task 3: 创建字体排版 Token

**Files:**
- Create: `miniapp/src/styles/tokens/_typography.scss`

**Step 1: 创建字体变量文件**

```scss
// miniapp/src/styles/tokens/_typography.scss
// 字体排版系统

// ========================================
// 字体家族
// ========================================

$font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
$font-family-mono: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;

// ========================================
// 字体大小 (使用 rpx 单位适配小程序)
// ========================================

$font-size-xs: 20rpx;     // 10px
$font-size-sm: 24rpx;     // 12px
$font-size-base: 28rpx;   // 14px
$font-size-lg: 32rpx;     // 16px
$font-size-xl: 36rpx;     // 18px
$font-size-2xl: 40rpx;    // 20px
$font-size-3xl: 48rpx;    // 24px
$font-size-4xl: 56rpx;    // 28px

// ========================================
// 字重
// ========================================

$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;

// ========================================
// 行高
// ========================================

$line-height-tight: 1.25;
$line-height-base: 1.5;
$line-height-relaxed: 1.75;

// ========================================
// 字间距
// ========================================

$letter-spacing-tight: -0.02em;
$letter-spacing-normal: 0;
$letter-spacing-wide: 0.02em;
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/tokens/_typography.scss
git commit -m "feat(miniapp): add typography tokens"
```

---

## Task 4: 创建间距 Token

**Files:**
- Create: `miniapp/src/styles/tokens/_spacing.scss`

**Step 1: 创建间距变量文件**

```scss
// miniapp/src/styles/tokens/_spacing.scss
// 间距系统

// ========================================
// 基础间距单位 (1 unit = 4rpx)
// ========================================

$spacing-unit: 4rpx;

// ========================================
// 间距 Scale (0-16)
// ========================================

$spacing-0: 0;
$spacing-1: 4rpx;       // 2px
$spacing-2: 8rpx;       // 4px
$spacing-3: 12rpx;      // 6px
$spacing-4: 16rpx;      // 8px
$spacing-5: 20rpx;      // 10px
$spacing-6: 24rpx;      // 12px
$spacing-8: 32rpx;      // 16px
$spacing-10: 40rpx;     // 20px
$spacing-12: 48rpx;     // 24px
$spacing-16: 64rpx;     // 32px
$spacing-20: 80rpx;     // 40px
$spacing-24: 96rpx;     // 48px

// ========================================
// 页面边距
// ========================================

$page-padding-x: 24rpx;
$page-padding-y: 24rpx;

// ========================================
// 组件内边距
// ========================================

$padding-card: 24rpx;
$padding-section: 32rpx;

// ========================================
// 组件间距
// ========================================

$gap-inline: 12rpx;     // 行内元素间距
$gap-block: 16rpx;      // 块级元素间距
$gap-section: 24rpx;    // 区块间距
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/tokens/_spacing.scss
git commit -m "feat(miniapp): add spacing tokens"
```

---

## Task 5: 创建玻璃效果 Mixins

**Files:**
- Create: `miniapp/src/styles/_glass.scss`

**Step 1: 创建玻璃效果文件**

```scss
// miniapp/src/styles/_glass.scss
// 液态玻璃效果 Mixins

// ========================================
// 标准玻璃卡片
// ========================================

@mixin glass-card($prominent: false) {
  background: if($prominent, var(--bg-glass-prominent), var(--bg-glass-standard));
  backdrop-filter: blur(20rpx);
  -webkit-backdrop-filter: blur(20rpx);
  border: 1rpx solid var(--border-regular);
  border-top-color: var(--border-glow);
  border-radius: 16rpx;
}

// ========================================
// 玻璃导航栏
// ========================================

@mixin glass-nav {
  background: var(--bg-glass-prominent);
  backdrop-filter: blur(30rpx);
  -webkit-backdrop-filter: blur(30rpx);
  border-bottom: 1rpx solid var(--border-subtle);
}

// ========================================
// 语义色玻璃适配
// 当语义色放置在毛玻璃效果之上时，添加 5% 白色叠加层
// ========================================

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

// ========================================
// 玻璃按钮
// ========================================

@mixin glass-button {
  @include glass-card();
  backdrop-filter: blur(10rpx);
  color: var(--text-primary);
  padding: 20rpx 40rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  transition: all 0.2s;

  &:active {
    transform: scale(0.97);
  }
}

// ========================================
// 玻璃输入框
// ========================================

@mixin glass-input {
  background: var(--bg-glass-standard);
  backdrop-filter: blur(10rpx);
  -webkit-backdrop-filter: blur(10rpx);
  border: 1rpx solid var(--border-regular);
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
  color: var(--text-primary);
  transition: border-color 0.2s;

  &:focus {
    border-color: var(--brand-primary);
  }

  &::placeholder {
    color: var(--text-tertiary);
  }
}
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/_glass.scss
git commit -m "feat(miniapp): add glass effect mixins"
```

---

## Task 6: 创建动态效果文件

**Files:**
- Create: `miniapp/src/styles/tokens/_animations.scss`

**Step 1: 创建动画文件**

```scss
// miniapp/src/styles/tokens/_animations.scss
// 动态效果系统

// ========================================
// AI 呼吸效果 - 3s 周期色相偏移
// ========================================

@keyframes breathe {
  0%, 100% {
    filter: hue-rotate(0deg);
  }
  50% {
    filter: hue-rotate(15deg);
  }
}

.ai-breathing {
  animation: breathe 3s ease-in-out infinite;
}

// ========================================
// 流光效果 - 渐变位置动画
// ========================================

@keyframes shimmer {
  0% {
    background-position: -200% center;
  }
  100% {
    background-position: 200% center;
  }
}

.ai-shimmer {
  background: $gradient-ai-core;
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

// ========================================
// 按压反馈
// ========================================

@keyframes press {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.97);
  }
  100% {
    transform: scale(1);
  }
}

.btn-press:active {
  animation: press 0.15s ease-out;
}

// ========================================
// 淡入动画
// ========================================

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}

// ========================================
// 从下滑入
// ========================================

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up {
  animation: slideUp 0.3s ease-out;
}

// ========================================
// 脉冲效果 (用于加载状态)
// ========================================

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

// ========================================
// 旋转加载
// ========================================

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

// ========================================
// 过渡时间
// ========================================

$transition-fast: 0.15s;
$transition-base: 0.2s;
$transition-slow: 0.3s;

// ========================================
// 缓动函数
// ========================================

$ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
$ease-out: cubic-bezier(0, 0, 0.2, 1);
$ease-in: cubic-bezier(0.4, 0, 1, 1);
$ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/tokens/_animations.scss
git commit -m "feat(miniapp): add animation tokens and keyframes"
```

---

## Task 7: 创建阴影 Token

**Files:**
- Create: `miniapp/src/styles/tokens/_shadows.scss`

**Step 1: 创建阴影文件**

```scss
// miniapp/src/styles/tokens/_shadows.scss
// 阴影系统

// ========================================
// 基础阴影
// ========================================

$shadow-sm: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
$shadow-base: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
$shadow-lg: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
$shadow-xl: 0 16rpx 48rpx rgba(0, 0, 0, 0.16);

// ========================================
// 内阴影
// ========================================

$shadow-inner: inset 0 2rpx 4rpx rgba(0, 0, 0, 0.06);

// ========================================
// 玻璃阴影 (配合毛玻璃效果使用)
// ========================================

$shadow-glass: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);

// ========================================
// 品牌色阴影 (用于强调元素)
// ========================================

$shadow-brand: 0 4rpx 16rpx rgba($brand-primary, 0.3);
$shadow-brand-lg: 0 8rpx 32rpx rgba($brand-primary, 0.25);

// ========================================
// 暗黑模式阴影
// ========================================

$shadow-sm-dark: 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
$shadow-base-dark: 0 4rpx 16rpx rgba(0, 0, 0, 0.4);
$shadow-lg-dark: 0 8rpx 32rpx rgba(0, 0, 0, 0.5);
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/tokens/_shadows.scss
git commit -m "feat(miniapp): add shadow tokens"
```

---

## Task 8: 创建主题系统

**Files:**
- Create: `miniapp/src/styles/themes/_light.scss`
- Create: `miniapp/src/styles/themes/_dark.scss`
- Create: `miniapp/src/styles/themes/_index.scss`

**Step 1: 创建浅色主题**

```scss
// miniapp/src/styles/themes/_light.scss
// 浅色主题变量

:root,
.theme-light {
  // 背景
  --bg-base: #{$bg-base};
  --bg-glass-subtle: #{$bg-glass-subtle};
  --bg-glass-standard: #{$bg-glass-standard};
  --bg-glass-prominent: #{$bg-glass-prominent};

  // 文字
  --text-primary: #{$text-primary};
  --text-secondary: #{$text-secondary};
  --text-tertiary: #{$text-tertiary};
  --text-disabled: #{$text-disabled};

  // 边框
  --border-subtle: #{$border-subtle};
  --border-regular: #{$border-regular};
  --border-glow: #{$border-glow};

  // 品牌色
  --brand-primary: #{$brand-primary};
  --brand-secondary: #{$brand-secondary};

  // 阴影
  --shadow-sm: #{$shadow-sm};
  --shadow-base: #{$shadow-base};
  --shadow-lg: #{$shadow-lg};
}
```

**Step 2: 创建暗黑主题**

```scss
// miniapp/src/styles/themes/_dark.scss
// 暗黑主题变量

:root,
.theme-dark {
  // 背景
  --bg-base: #{$bg-base-dark};
  --bg-glass-subtle: #{$bg-glass-subtle-dark};
  --bg-glass-standard: #{$bg-glass-standard-dark};
  --bg-glass-prominent: #{$bg-glass-prominent-dark};

  // 文字
  --text-primary: #{$text-primary-dark};
  --text-secondary: #{$text-secondary-dark};
  --text-tertiary: #{$text-tertiary-dark};
  --text-disabled: #{$text-disabled-dark};

  // 边框
  --border-subtle: #{$border-subtle-dark};
  --border-regular: #{$border-regular-dark};
  --border-glow: #{$border-glow-dark};

  // 品牌色 (暗黑模式下明度提升)
  --brand-primary: #{$brand-primary-dark};
  --brand-secondary: #{$brand-secondary-dark};

  // 阴影
  --shadow-sm: #{$shadow-sm-dark};
  --shadow-base: #{$shadow-base-dark};
  --shadow-lg: #{$shadow-lg-dark};
}
```

**Step 3: 创建主题入口**

```scss
// miniapp/src/styles/themes/_index.scss
// 主题切换系统

// 默认浅色主题
@import 'light';

// 自动跟随系统暗黑模式
@media (prefers-color-scheme: dark) {
  :root:not(.theme-light) {
    @import 'dark';
  }
}
```

**Step 4: Commit**

```bash
git add miniapp/src/styles/themes/
git commit -m "feat(miniapp): add theme system with dark mode support"
```

---

## Task 9: 创建 Token 汇总导出

**Files:**
- Create: `miniapp/src/styles/tokens/_index.scss`

**Step 1: 创建 Token 入口文件**

```scss
// miniapp/src/styles/tokens/_index.scss
// 设计系统 Token 汇总导出

// 色彩
@import 'colors';

// 字体排版
@import 'typography';

// 间距
@import 'spacing';

// 阴影
@import 'shadows';

// 动画
@import 'animations';
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/tokens/_index.scss
git commit -m "feat(miniapp): add tokens index file"
```

---

## Task 10: 创建工具类文件

**Files:**
- Create: `miniapp/src/styles/_utilities.scss`

**Step 1: 创建工具类文件**

```scss
// miniapp/src/styles/_utilities.scss
// 工具类

// ========================================
// 显示/隐藏
// ========================================

.hidden {
  display: none !important;
}

.invisible {
  visibility: hidden !important;
}

// ========================================
// 文字截断
// ========================================

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

// ========================================
// Flex 布局
// ========================================

.flex {
  display: flex;
}

.flex-col {
  flex-direction: column;
}

.flex-wrap {
  flex-wrap: wrap;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.justify-between {
  justify-content: space-between;
}

.flex-1 {
  flex: 1;
}

// ========================================
// 文字对齐
// ========================================

.text-left {
  text-align: left;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

// ========================================
// 文字颜色
// ========================================

.text-primary {
  color: var(--text-primary);
}

.text-secondary {
  color: var(--text-secondary);
}

.text-tertiary {
  color: var(--text-tertiary);
}

.text-brand {
  color: var(--brand-primary);
}

.text-success {
  color: $semantic-success;
}

.text-error {
  color: $semantic-error;
}

.text-warning {
  color: $semantic-warning;
}

// ========================================
// 间距工具类
// ========================================

.mt-1 { margin-top: $spacing-1; }
.mt-2 { margin-top: $spacing-2; }
.mt-4 { margin-top: $spacing-4; }
.mt-6 { margin-top: $spacing-6; }
.mt-8 { margin-top: $spacing-8; }

.mb-1 { margin-bottom: $spacing-1; }
.mb-2 { margin-bottom: $spacing-2; }
.mb-4 { margin-bottom: $spacing-4; }
.mb-6 { margin-bottom: $spacing-6; }
.mb-8 { margin-bottom: $spacing-8; }

.p-4 { padding: $spacing-4; }
.p-6 { padding: $spacing-6; }
.p-8 { padding: $spacing-8; }

// ========================================
// 圆角
// ========================================

.rounded {
  border-radius: 8rpx;
}

.rounded-lg {
  border-radius: 16rpx;
}

.rounded-full {
  border-radius: 9999rpx;
}
```

**Step 2: Commit**

```bash
git add miniapp/src/styles/_utilities.scss
git commit -m "feat(miniapp): add utility classes"
```

---

## Task 11: 创建全局样式入口

**Files:**
- Create: `miniapp/src/styles/index.scss`
- Modify: `miniapp/src/uni.scss`

**Step 1: 创建全局样式入口**

```scss
// miniapp/src/styles/index.scss
// 设计系统全局样式入口

// Token 变量
@import 'tokens';

// 主题系统
@import 'themes';

// 玻璃效果
@import 'glass';

// 工具类
@import 'utilities';

// ========================================
// 全局基础样式
// ========================================

page {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: $font-family-base;
  font-size: $font-size-base;
  line-height: $line-height-base;
}

// ========================================
// 安全区域
// ========================================

.safe-area-top {
  padding-top: env(safe-area-inset-top);
}

.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}

// ========================================
// 滚动容器
// ========================================

.scroll-container {
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
```

**Step 2: 更新 uni.scss 引入设计系统**

```scss
// miniapp/src/uni.scss
// uni-app 内置样式变量

// 引入设计系统
@import './styles/index.scss';

// 以下为 uni-app 默认变量（保留兼容性）

/* 行为相关颜色 */
$uni-color-primary: $brand-primary;
$uni-color-success: $semantic-success;
$uni-color-warning: $semantic-warning;
$uni-color-error: $semantic-error;

/* 文字基本颜色 */
$uni-text-color: #333;
$uni-text-color-inverse: #fff;
$uni-text-color-grey: #999;
$uni-text-color-placeholder: #808080;
$uni-text-color-disable: #c0c0c0;

/* 背景颜色 */
$uni-bg-color: #fff;
$uni-bg-color-grey: #f8f8f8;
$uni-bg-color-hover: #f1f1f1;
$uni-bg-color-mask: rgba(0, 0, 0, 0.4);

/* 边框颜色 */
$uni-border-color: #c8c7cc;

/* 尺寸变量 */
$uni-font-size-sm: 12px;
$uni-font-size-base: 14px;
$uni-font-size-lg: 16px;

$uni-border-radius-sm: 2px;
$uni-border-radius-base: 3px;
$uni-border-radius-lg: 6px;
$uni-border-radius-circle: 50%;

$uni-spacing-row-sm: 5px;
$uni-spacing-row-base: 10px;
$uni-spacing-row-lg: 15px;

$uni-spacing-col-sm: 4px;
$uni-spacing-col-base: 8px;
$uni-spacing-col-lg: 12px;

$uni-opacity-disabled: 0.3;
```

**Step 3: Commit**

```bash
git add miniapp/src/styles/index.scss miniapp/src/uni.scss
git commit -m "feat(miniapp): create global styles entry and update uni.scss"
```

---

## Task 12: 创建 PdButton 组件

**Files:**
- Create: `miniapp/src/components/ui/PdButton.vue`

**Step 1: 创建按钮组件**

```vue
<!-- miniapp/src/components/ui/PdButton.vue -->
<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    :loading="loading"
    @click="handleClick"
  >
    <view v-if="loading" class="pd-btn__loading">
      <view class="pd-btn__spinner" />
    </view>
    <slot v-else />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'outline' | 'link' | 'glass'
    size?: 'sm' | 'md' | 'lg'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
    block: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClasses = computed(() => [
  'pd-btn',
  `pd-btn--${props.variant}`,
  `pd-btn--${props.size}`,
  {
    'pd-btn--block': props.block,
    'pd-btn--loading': props.loading,
  },
])

function handleClick(event: MouseEvent) {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style lang="scss">
.pd-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  font-weight: $font-weight-medium;
  transition: all $transition-base $ease-out;
  cursor: pointer;

  // 尺寸
  &--sm {
    padding: 12rpx 24rpx;
    font-size: $font-size-sm;
    border-radius: 8rpx;
  }

  &--md {
    padding: 20rpx 40rpx;
    font-size: $font-size-base;
    border-radius: 12rpx;
  }

  &--lg {
    padding: 28rpx 56rpx;
    font-size: $font-size-lg;
    border-radius: 16rpx;
  }

  // 变体
  &--primary {
    background: $gradient-brand;
    color: #fff;

    &:active {
      opacity: 0.9;
      transform: scale(0.97);
    }
  }

  &--secondary {
    background: $brand-secondary;
    color: #fff;

    &:active {
      opacity: 0.9;
      transform: scale(0.97);
    }
  }

  &--outline {
    background: transparent;
    color: var(--brand-primary);
    border: 1rpx solid var(--brand-primary);

    &:active {
      background: rgba($brand-primary, 0.1);
      transform: scale(0.97);
    }
  }

  &--link {
    background: transparent;
    color: var(--brand-primary);
    padding: 0;

    &:active {
      opacity: 0.7;
    }
  }

  &--glass {
    @include glass-card();
    color: var(--text-primary);

    &:active {
      transform: scale(0.97);
    }
  }

  // 块级按钮
  &--block {
    display: flex;
    width: 100%;
  }

  // 禁用状态
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  // 加载状态
  &--loading {
    pointer-events: none;
  }

  &__loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__spinner {
    width: 32rpx;
    height: 32rpx;
    border: 3rpx solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdButton.vue
git commit -m "feat(miniapp): add PdButton component"
```

---

## Task 13: 创建 PdCard 组件

**Files:**
- Create: `miniapp/src/components/ui/PdCard.vue`

**Step 1: 创建卡片组件**

```vue
<!-- miniapp/src/components/ui/PdCard.vue -->
<template>
  <view :class="cardClasses" @click="handleClick">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    level?: 'subtle' | 'standard' | 'prominent'
    hoverable?: boolean
    padding?: 'none' | 'sm' | 'md' | 'lg'
  }>(),
  {
    level: 'standard',
    hoverable: false,
    padding: 'md',
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const cardClasses = computed(() => [
  'pd-card',
  `pd-card--${props.level}`,
  `pd-card--padding-${props.padding}`,
  {
    'pd-card--hoverable': props.hoverable,
  },
])

function handleClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<style lang="scss">
.pd-card {
  transition: all $transition-base $ease-out;

  // 层级
  &--subtle {
    background: var(--bg-glass-subtle);
    border: none;
  }

  &--standard {
    @include glass-card();
  }

  &--prominent {
    @include glass-card($prominent: true);
  }

  // 内边距
  &--padding-none {
    padding: 0;
  }

  &--padding-sm {
    padding: 16rpx;
  }

  &--padding-md {
    padding: 24rpx;
  }

  &--padding-lg {
    padding: 32rpx;
  }

  // 可悬停
  &--hoverable {
    cursor: pointer;

    &:active {
      transform: scale(0.98);
      opacity: 0.95;
    }
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdCard.vue
git commit -m "feat(miniapp): add PdCard component"
```

---

## Task 14: 创建 PdInput 组件

**Files:**
- Create: `miniapp/src/components/ui/PdInput.vue`

**Step 1: 创建输入框组件**

```vue
<!-- miniapp/src/components/ui/PdInput.vue -->
<template>
  <view class="pd-input-wrapper">
    <view v-if="$slots.prefix" class="pd-input__prefix">
      <slot name="prefix" />
    </view>
    <input
      class="pd-input"
      :class="inputClasses"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxlength"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    />
    <view v-if="$slots.suffix" class="pd-input__suffix">
      <slot name="suffix" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    type?: 'text' | 'number' | 'password' | 'tel'
    placeholder?: string
    disabled?: boolean
    maxlength?: number
    error?: boolean
  }>(),
  {
    modelValue: '',
    type: 'text',
    placeholder: '',
    disabled: false,
    error: false,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}>()

const isFocused = ref(false)

const inputClasses = computed(() => [
  {
    'pd-input--focused': isFocused.value,
    'pd-input--disabled': props.disabled,
    'pd-input--error': props.error,
  },
])

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleFocus(event: FocusEvent) {
  isFocused.value = true
  emit('focus', event)
}

function handleBlur(event: FocusEvent) {
  isFocused.value = false
  emit('blur', event)
}
</script>

<style lang="scss">
.pd-input-wrapper {
  display: flex;
  align-items: center;
  @include glass-input();
}

.pd-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: inherit;
  color: inherit;

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--error {
    border-color: $semantic-error !important;
  }
}

.pd-input__prefix,
.pd-input__suffix {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
}

.pd-input__prefix {
  margin-right: 12rpx;
}

.pd-input__suffix {
  margin-left: 12rpx;
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdInput.vue
git commit -m "feat(miniapp): add PdInput component"
```

---

## Task 15: 创建 PdBadge 组件

**Files:**
- Create: `miniapp/src/components/ui/PdBadge.vue`

**Step 1: 创建徽标组件**

```vue
<!-- miniapp/src/components/ui/PdBadge.vue -->
<template>
  <view :class="badgeClasses">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'
    size?: 'sm' | 'md'
    glass?: boolean
  }>(),
  {
    type: 'default',
    size: 'md',
    glass: false,
  }
)

const badgeClasses = computed(() => [
  'pd-badge',
  `pd-badge--${props.type}`,
  `pd-badge--${props.size}`,
  {
    'pd-badge--glass': props.glass,
  },
])
</script>

<style lang="scss">
.pd-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: $font-weight-medium;
  border-radius: 9999rpx;

  // 尺寸
  &--sm {
    padding: 4rpx 12rpx;
    font-size: $font-size-xs;
  }

  &--md {
    padding: 8rpx 20rpx;
    font-size: $font-size-sm;
  }

  // 类型
  &--default {
    background: rgba(0, 0, 0, 0.06);
    color: var(--text-secondary);
  }

  &--primary {
    background: rgba($brand-primary, 0.15);
    color: var(--brand-primary);
  }

  &--success {
    background: rgba($semantic-success, 0.15);
    color: $semantic-success;
  }

  &--error {
    background: rgba($semantic-error, 0.15);
    color: $semantic-error;
  }

  &--warning {
    background: rgba($semantic-warning, 0.15);
    color: $semantic-warning;
  }

  &--info {
    background: rgba($semantic-info, 0.15);
    color: $semantic-info;
  }

  // 玻璃效果
  &--glass {
    @include glass-card();
    backdrop-filter: blur(8rpx);

    &.pd-badge--primary {
      @include semantic-glass(rgba($brand-primary, 0.15));
    }

    &.pd-badge--success {
      @include semantic-glass(rgba($semantic-success, 0.15));
    }
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdBadge.vue
git commit -m "feat(miniapp): add PdBadge component"
```

---

## Task 16: 创建 PdAvatar 组件

**Files:**
- Create: `miniapp/src/components/ui/PdAvatar.vue`

**Step 1: 创建头像组件**

```vue
<!-- miniapp/src/components/ui/PdAvatar.vue -->
<template>
  <view :class="avatarClasses" @click="handleClick">
    <image
      v-if="src"
      class="pd-avatar__image"
      :src="src"
      mode="aspectFill"
    />
    <text v-else class="pd-avatar__fallback">{{ fallbackText }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    name?: string
    glass?: boolean
  }>(),
  {
    src: '',
    size: 'md',
    name: '',
    glass: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const avatarClasses = computed(() => [
  'pd-avatar',
  `pd-avatar--${props.size}`,
  {
    'pd-avatar--glass': props.glass,
    'pd-avatar--has-image': !!props.src,
  },
])

const fallbackText = computed(() => {
  if (!props.name) return '?'
  return props.name.charAt(0).toUpperCase()
})

function handleClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<style lang="scss">
.pd-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba($brand-primary, 0.15);
  color: var(--brand-primary);
  overflow: hidden;

  // 尺寸
  &--xs {
    width: 48rpx;
    height: 48rpx;
    font-size: $font-size-xs;
  }

  &--sm {
    width: 64rpx;
    height: 64rpx;
    font-size: $font-size-sm;
  }

  &--md {
    width: 88rpx;
    height: 88rpx;
    font-size: $font-size-lg;
  }

  &--lg {
    width: 120rpx;
    height: 120rpx;
    font-size: $font-size-xl;
  }

  &--xl {
    width: 160rpx;
    height: 160rpx;
    font-size: $font-size-2xl;
  }

  // 玻璃效果
  &--glass {
    border: 2rpx solid var(--border-glow);
    background: var(--bg-glass-standard);
    backdrop-filter: blur(10rpx);
  }

  &__image {
    width: 100%;
    height: 100%;
  }

  &__fallback {
    font-weight: $font-weight-semibold;
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdAvatar.vue
git commit -m "feat(miniapp): add PdAvatar component"
```

---

## Task 17: 创建 PdNavBar 组件

**Files:**
- Create: `miniapp/src/components/ui/PdNavBar.vue`

**Step 1: 创建导航栏组件**

```vue
<!-- miniapp/src/components/ui/PdNavBar.vue -->
<template>
  <view class="pd-navbar" :style="{ paddingTop: safeAreaTop + 'px' }">
    <view class="pd-navbar__content">
      <view class="pd-navbar__left" @click="handleBack">
        <slot name="left">
          <view v-if="showBack" class="pd-navbar__back">
            <text class="pd-navbar__back-icon">‹</text>
          </view>
        </slot>
      </view>
      <view class="pd-navbar__title">
        <slot>{{ title }}</slot>
      </view>
      <view class="pd-navbar__right">
        <slot name="right" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = withDefaults(
  defineProps<{
    title?: string
    showBack?: boolean
  }>(),
  {
    title: '',
    showBack: true,
  }
)

const emit = defineEmits<{
  back: []
}>()

const safeAreaTop = ref(0)

onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  safeAreaTop.value = systemInfo.safeAreaInsets?.top || 0
})

function handleBack() {
  if (props.showBack) {
    emit('back')
    uni.navigateBack()
  }
}
</script>

<style lang="scss">
.pd-navbar {
  @include glass-nav();
  position: sticky;
  top: 0;
  z-index: 100;

  &__content {
    display: flex;
    align-items: center;
    height: 88rpx;
    padding: 0 24rpx;
  }

  &__left,
  &__right {
    flex-shrink: 0;
    width: 80rpx;
  }

  &__title {
    flex: 1;
    text-align: center;
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__back {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56rpx;
    height: 56rpx;
    cursor: pointer;

    &:active {
      opacity: 0.7;
    }
  }

  &__back-icon {
    font-size: 48rpx;
    color: var(--text-primary);
    line-height: 1;
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdNavBar.vue
git commit -m "feat(miniapp): add PdNavBar component"
```

---

## Task 18: 创建 PdEmpty 组件

**Files:**
- Create: `miniapp/src/components/ui/PdEmpty.vue`

**Step 1: 创建空状态组件**

```vue
<!-- miniapp/src/components/ui/PdEmpty.vue -->
<template>
  <view class="pd-empty">
    <view v-if="$slots.icon" class="pd-empty__icon">
      <slot name="icon" />
    </view>
    <text v-else class="pd-empty__default-icon">{{ defaultIcon }}</text>
    <text v-if="title" class="pd-empty__title">{{ title }}</text>
    <text v-if="description" class="pd-empty__description">{{ description }}</text>
    <view v-if="$slots.action" class="pd-empty__action">
      <slot name="action" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title?: string
    description?: string
    type?: 'default' | 'search' | 'network' | 'error'
  }>(),
  {
    title: '暂无数据',
    description: '',
    type: 'default',
  }
)

const defaultIcon = computed(() => {
  const icons = {
    default: '📭',
    search: '🔍',
    network: '📡',
    error: '⚠️',
  }
  return icons[props.type]
})
</script>

<style lang="scss">
.pd-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;

  &__icon,
  &__default-icon {
    margin-bottom: 24rpx;
  }

  &__default-icon {
    font-size: 80rpx;
  }

  &__title {
    font-size: $font-size-lg;
    font-weight: $font-weight-medium;
    color: var(--text-secondary);
    margin-bottom: 12rpx;
  }

  &__description {
    font-size: $font-size-sm;
    color: var(--text-tertiary);
    text-align: center;
  }

  &__action {
    margin-top: 32rpx;
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdEmpty.vue
git commit -m "feat(miniapp): add PdEmpty component"
```

---

## Task 19: 创建 PdLoading 组件

**Files:**
- Create: `miniapp/src/components/ui/PdLoading.vue`

**Step 1: 创建加载组件**

```vue
<!-- miniapp/src/components/ui/PdLoading.vue -->
<template>
  <view class="pd-loading" :class="{ 'pd-loading--fullpage': fullpage }">
    <view class="pd-loading__spinner" :class="{ 'ai-breathing': ai }">
      <view v-for="i in 3" :key="i" class="pd-loading__dot" :style="{ animationDelay: (i - 1) * 0.15 + 's' }" />
    </view>
    <text v-if="text" class="pd-loading__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string
    fullpage?: boolean
    ai?: boolean
  }>(),
  {
    text: '',
    fullpage: false,
    ai: false,
  }
)
</script>

<style lang="scss">
@keyframes loadingDot {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.pd-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;

  &--fullpage {
    position: fixed;
    inset: 0;
    background: var(--bg-base);
    z-index: 1000;
  }

  &__spinner {
    display: flex;
    gap: 12rpx;
  }

  &__dot {
    width: 16rpx;
    height: 16rpx;
    border-radius: 50%;
    background: $gradient-brand;
    animation: loadingDot 1.4s ease-in-out infinite;
  }

  &__text {
    margin-top: 20rpx;
    font-size: $font-size-sm;
    color: var(--text-secondary);
  }
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/PdLoading.vue
git commit -m "feat(miniapp): add PdLoading component with AI breathing effect"
```

---

## Task 20: 创建组件库导出

**Files:**
- Create: `miniapp/src/components/ui/index.ts`

**Step 1: 创建组件导出文件**

```typescript
// miniapp/src/components/ui/index.ts
// UI 组件库统一导出

export { default as PdButton } from './PdButton.vue'
export { default as PdCard } from './PdCard.vue'
export { default as PdInput } from './PdInput.vue'
export { default as PdBadge } from './PdBadge.vue'
export { default as PdAvatar } from './PdAvatar.vue'
export { default as PdNavBar } from './PdNavBar.vue'
export { default as PdEmpty } from './PdEmpty.vue'
export { default as PdLoading } from './PdLoading.vue'

// 组件类型导出
export type { } from './PdButton.vue'
```

**Step 2: Commit**

```bash
git add miniapp/src/components/ui/index.ts
git commit -m "feat(miniapp): add UI components index export"
```

---

## Task 21: 迁移首页 (Phase 1 - index.vue)

**Files:**
- Modify: `miniapp/src/pages/index.vue`

**Step 1: 更新首页样式使用设计系统**

替换现有的硬编码颜色为设计系统变量，应用玻璃效果。

主要修改：
1. `.user-bar` - 应用 `@include glass-card()`
2. `.btn-primary` - 使用 `$gradient-brand`
3. `.mood-item.active` - 使用 `$brand-primary`
4. `.progress-inner` - 使用 `$gradient-brand`
5. 所有颜色值替换为设计变量

**Step 2: 测试页面显示**

Run:
```bash
cd miniapp && npm run dev
```

Expected: 页面正常显示，玻璃效果生效

**Step 3: Commit**

```bash
git add miniapp/src/pages/index.vue
git commit -m "refactor(miniapp): migrate index page to design system"
```

---

## Task 22: 迁移个人中心页 (Phase 1 - profile/index.vue)

**Files:**
- Modify: `miniapp/src/pages/profile/index.vue`

**Step 1: 更新个人中心页样式**

主要修改：
1. `.user-header` - 使用 `$gradient-brand` 背景
2. `.user-points-badge` - 应用玻璃效果
3. `.btn-primary` - 使用设计系统按钮样式
4. `.btn-outline` - 使用设计系统按钮样式
5. `.card` - 应用 `@include glass-card()`

**Step 2: Commit**

```bash
git add miniapp/src/pages/profile/index.vue
git commit -m "refactor(miniapp): migrate profile page to design system"
```

---

## Task 23: 迁移登录页 (Phase 1 - login/index.vue)

**Files:**
- Modify: `miniapp/src/pages/login/index.vue`

**Step 1: 更新登录页样式**

主要修改：
1. 应用玻璃背景
2. 使用 PdButton 组件
3. 使用设计系统颜色变量

**Step 2: Commit**

```bash
git add miniapp/src/pages/login/index.vue
git commit -m "refactor(miniapp): migrate login page to design system"
```

---

## Task 24: 验证暗黑模式

**Step 1: 测试暗黑模式切换**

在微信开发者工具中切换暗黑模式，验证：
- 所有页面背景色正确切换
- 文字颜色对比度符合标准
- 玻璃效果在暗黑模式下正常

**Step 2: 修复暗黑模式问题（如有）**

**Step 3: 最终 Commit**

```bash
git add miniapp/src/
git commit -m "feat(miniapp): complete design system implementation"
```

---

## 实现总结

完成后将实现：

1. **样式系统**
   - `styles/tokens/` - 色彩、字体、间距、阴影、动画
   - `styles/themes/` - 浅色/暗黑主题
   - `styles/_glass.scss` - 玻璃效果 mixins
   - `styles/_utilities.scss` - 工具类

2. **UI 组件库**
   - `PdButton` - 按钮组件
   - `PdCard` - 卡片组件
   - `PdInput` - 输入框组件
   - `PdBadge` - 徽标组件
   - `PdAvatar` - 头像组件
   - `PdNavBar` - 导航栏组件
   - `PdEmpty` - 空状态组件
   - `PdLoading` - 加载组件

3. **页面迁移**
   - Phase 1: 首页、个人中心、登录页
