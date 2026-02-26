# 积分商品管理 E2E 测试设计方案

## 概述

为 admin-web 后台管理系统的积分商品管理模块实现端到端（E2E）浏览器自动化测试，覆盖商品的创建、编辑、列表、删除等完整流程，包括单规格和多规格商品的测试。

## 技术选型

- **测试框架**: Playwright
- **设计模式**: Page Object Model (POM)
- **运行环境**: 自动启动本地开发服务器
- **数据策略**: 隔离的测试数据，每次测试独立创建/清理

## 架构设计

### 目录结构

```
admin-web/
├── playwright.config.ts          # Playwright 配置
├── tests/
│   └── e2e/
│       ├── auth.setup.ts         # 登录状态保存（一次登录，复用会话）
│       ├── fixtures/
│       │   ├── index.ts          # Playwright fixtures 定义
│       │   └── test-data.ts      # 测试数据常量
│       ├── pages/
│       │   ├── BasePage.ts       # 基础页面类
│       │   ├── LoginPage.ts      # 登录页
│       │   ├── ProductListPage.ts # 商品列表页
│       │   └── ProductFormPage.ts # 商品表单页（新增/编辑）
│       ├── specs/
│       │   ├── product-create.spec.ts   # 创建商品测试
│       │   ├── product-edit.spec.ts     # 编辑商品测试
│       │   ├── product-list.spec.ts     # 列表页测试
│       │   ├── product-sku-single.spec.ts  # 单规格测试
│       │   └── product-sku-multi.spec.ts   # 多规格测试
│       └── utils/
│           └── helpers.ts        # 通用工具函数
```

### 核心设计原则

1. **认证复用**: 使用 Playwright 的 `storageState` 保存登录状态，避免每个测试重复登录
2. **数据隔离**: 每个测试套件独立创建/清理测试数据，使用随机后缀避免冲突
3. **Page Object**: 封装页面元素定位和操作，提高可维护性
4. **断言封装**: 自定义断言方法，提高测试可读性

## Page Object 设计

### BasePage (基础页面类)

```typescript
// tests/e2e/pages/BasePage.ts
export abstract class BasePage {
  readonly page: Page;

  // 通用导航
  async goto(path: string): Promise<void>;
  async waitForPageLoad(): Promise<void>;

  // 通用操作
  async clickElement(selector: string): Promise<void>;
  async fillInput(selector: string, value: string): Promise<void>;
  async selectOption(selector: string, value: string): Promise<void>;

  // 通用断言
  async expectToast(message: string): Promise<void>;
  async expectElementVisible(selector: string): Promise<void>;
}
```

### ProductFormPage (商品表单页)

```typescript
// tests/e2e/pages/ProductFormPage.ts
export class ProductFormPage extends BasePage {
  // 表单字段定位器
  readonly nameInput: Locator;
  readonly typeSelect: Locator;
  readonly categorySelect: Locator;
  readonly descriptionTextarea: Locator;
  readonly skuToggle: Locator;
  readonly submitButton: Locator;

  // 核心操作
  async fillBasicInfo(data: ProductBasicInfo): Promise<void>;
  async uploadImages(imagePaths: string[]): Promise<void>;

  // SKU 操作
  async enableSku(): Promise<void>;
  async disableSku(): Promise<void>;
  async addSpecification(name: string, values: string[]): Promise<void>;
  async setSkuStock(skuCode: string, stock: number): Promise<void>;
  async setSkuPoints(skuCode: string, points: number): Promise<void>;

  // 提交
  async submit(): Promise<void>;
  async expectCreateSuccess(): Promise<void>;
  async expectValidationError(field: string): Promise<void>;
}
```

### ProductListPage (商品列表页)

```typescript
// tests/e2e/pages/ProductListPage.ts
export class ProductListPage extends BasePage {
  readonly searchInput: Locator;
  readonly searchButton: Locator;
  readonly table: Locator;
  readonly pagination: Locator;

  // 列表操作
  async searchByKeyword(keyword: string): Promise<void>;
  async clickCreateButton(): Promise<void>;
  async clickEditButton(productName: string): Promise<void>;
  async clickDeleteButton(productName: string): Promise<void>;
  async confirmDelete(): Promise<void>;

  // 断言
  async expectProductInList(name: string): Promise<void>;
  async expectProductNotInList(name: string): Promise<void>;
  async expectProductCount(count: number): Promise<void>;
}
```

## 测试用例覆盖

### 1. 商品创建测试 (`product-create.spec.ts`)

| 测试用例 | 描述 |
|---------|------|
| 创建实物商品（单规格） | 填写基本信息 + 上传图片 + 设置库存和积分 |
| 创建虚拟商品 | 选择虚拟商品类型，验证发货方式隐藏 |
| 创建自提商品 | 选择自提发货方式 |
| 必填字段校验 | 空商品名、空分类等验证提示 |
| 图片上传限制 | 超过6张图片时的限制 |
| 取消创建 | 点击取消返回列表页 |

### 2. 商品编辑测试 (`product-edit.spec.ts`)

| 测试用例 | 描述 |
|---------|------|
| 编辑商品基本信息 | 修改名称、描述、分类 |
| 修改商品状态 | 上架/下架切换 |
| 编辑后保存验证 | 确认修改已保存 |
| 未修改直接返回 | 无变更时返回列表 |

### 3. 商品列表测试 (`product-list.spec.ts`)

| 测试用例 | 描述 |
|---------|------|
| 列表加载 | 验证列表正常显示 |
| 搜索功能 | 按商品名搜索 |
| 筛选分类 | 按分类筛选商品 |
| 分页功能 | 翻页验证 |
| 删除商品 | 删除确认 + 列表更新 |
| 批量操作 | 批量上架/下架（如有） |

### 4. 单规格测试 (`product-sku-single.spec.ts`)

| 测试用例 | 描述 |
|---------|------|
| 禁用SKU模式 | 单规格商品直接设置库存和积分 |
| 库存设置 | 设置有限/无限库存 |
| 积分设置 | 设置兑换所需积分 |

### 5. 多规格测试 (`product-sku-multi.spec.ts`)

| 测试用例 | 描述 |
|---------|------|
| 启用SKU模式 | 打开SKU开关 |
| 添加单个规格 | 如：颜色（红、蓝、绿） |
| 添加多个规格 | 如：颜色 + 尺寸 |
| SKU组合生成 | 验证组合表格正确生成 |
| 编辑SKU信息 | 修改单个SKU的库存/积分 |
| 删除规格值 | 删除后组合自动更新 |
| 规格值重复校验 | 不允许重复规格值 |

## 测试数据与 Fixtures

### 测试数据常量 (`fixtures/test-data.ts`)

```typescript
export const TEST_PRODUCTS = {
  // 基础商品模板
  basicPhysical: {
    name: '测试实物商品',
    type: 'physical',
    shippingMethod: 'express',
    description: '这是一个测试商品',
    points: 100,
    stock: 50,
  },

  basicVirtual: {
    name: '测试虚拟商品',
    type: 'virtual',
    shippingMethod: 'no_shipping',
    description: '虚拟商品描述',
    points: 50,
  },

  // SKU 商品模板
  multiSkuProduct: {
    name: '测试多规格商品',
    specifications: [
      { name: '颜色', values: ['红色', '蓝色'] },
      { name: '尺寸', values: ['S', 'M', 'L'] },
    ],
  },
};

export const TEST_ADMIN = {
  username: 'admin',
  password: 'admin123',
};

// 生成唯一名称的工具函数
export function uniqueName(base: string): string {
  return `${base}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}
```

### Playwright Fixtures (`fixtures/index.ts`)

```typescript
import { test as base } from '@playwright/test';

// 自定义 fixtures
export const test = base.extend({
  // 已认证的页面（自动登录）
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.fill('[name="username"]', TEST_ADMIN.username);
    await page.fill('[name="password"]', TEST_ADMIN.password);
    await page.click('[type="submit"]');
    await page.waitForURL('**/admin/**');
    await use(page);
  },

  // 干净的商品列表页
  cleanProductList: async ({ authenticatedPage }, use) => {
    const listPage = new ProductListPage(authenticatedPage);
    await listPage.goto('/admin/point-shop');
    await use(listPage);
  },
});

export { expect } from '@playwright/test';
```

### 认证状态复用 (`auth.setup.ts`)

```typescript
// 在所有测试前执行一次登录，保存状态
import { test as setup, expect } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="username"]', TEST_ADMIN.username);
  await page.fill('[name="password"]', TEST_ADMIN.password);
  await page.click('[type="submit"]');
  await expect(page).toHaveURL(/.*admin.*/);

  // 保存登录状态到文件
  await page.context().storageState({ path: 'tests/e2e/.auth/admin.json' });
});
```

## 配置与执行

### Playwright 配置 (`playwright.config.ts`)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e/specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['list']],

  // 全局测试配置
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // 使用保存的认证状态
    storageState: 'tests/e2e/.auth/admin.json',
  },

  // 项目配置
  projects: [
    // 认证设置（最先执行）
    { name: 'setup', testMatch: /.*\.setup\.ts/ },

    // Chromium 测试
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],

  // 自动启动开发服务器
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5174',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

### package.json 脚本

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:report": "playwright show-report"
  }
}
```

### 需要安装的依赖

```bash
npm install -D @playwright/test
npx playwright install  # 安装浏览器
```

## 注意事项

1. **后端依赖**: E2E 测试需要后端服务运行，确保 `http://localhost:8000` 可访问
2. **测试账号**: 需要在测试数据库中预先创建测试管理员账号
3. **图片资源**: 测试图片上传需要准备测试图片文件
4. **清理策略**: 测试结束后应清理创建的测试数据，避免污染数据库
5. **CI 集成**: 在 CI 环境中需要调整 worker 数量和重试策略
