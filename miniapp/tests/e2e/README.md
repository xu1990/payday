# 微信小程序 E2E 测试

基于 `@dcloudio/uni-automator` 的微信小程序端到端自动化测试。

## 前置条件

### 1. 安装微信开发者工具

下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)

### 2. 开启自动化服务端口

1. 打开微信开发者工具
2. 进入 **设置 -> 安全设置**
3. 开启 **服务端口**

### 3. 配置环境变量（可选）

如果微信开发者工具不在默认路径，需要设置环境变量：

```bash
# macOS
export WECHAT_DEVTOOLS_PATH="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"

# Windows
set WECHAT_DEVTOOLS_PATH=C:\\Program Files (x86)\\Tencent\\webwechatdevtools\\cli.bat
```

## 运行测试

### 构建并运行 E2E 测试

```bash
# 从项目根目录
npm run test:miniapp:e2e

# 或从 miniapp 目录
cd miniapp
npm run build:test
```

### 单独运行 E2E 测试（需先构建）

```bash
cd miniapp

# 1. 构建小程序
npm run build

# 2. 运行 e2e 测试
npm run test:e2e
```

### 使用 UI 模式运行

```bash
npm run test:e2e:ui
```

### 监听模式（开发时使用）

```bash
npm run test:e2e:watch
```

## 测试文件结构

```
tests/e2e/
├── README.md              # 本文件
├── index.test.ts          # 测试入口，启动/关闭开发者工具
├── helpers.ts             # 测试辅助函数
├── splash.test.ts         # 启动与登录流程测试
├── navigation.test.ts     # Tab 导航与页面跳转测试
└── payday.test.ts         # 发薪日设置与工资记录测试
```

## 编写新的 E2E 测试

1. 在 `tests/e2e/` 目录下创建新的测试文件，如 `feature.test.ts`

2. 导入必要的模块：

```typescript
import { describe, it, expect, beforeAll } from 'vitest'
import type { MiniProgram } from '@dcloudio/uni-automator'
import { waitForPageLoad, delay } from './helpers'

let miniProgram: MiniProgram

describe('E2E: 新功能测试', () => {
  beforeAll(async () => {
    const { getMiniProgram } = await import('./index.test')
    miniProgram = getMiniProgram()
    // 跳转到测试页面
    await miniProgram.reLaunch('/pages/your-page/index')
    await delay(2000)
  }, 60000)

  it('应该显示页面', async () => {
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/your-page/index')
  })
})
```

## 可用的辅助函数

从 `helpers.ts` 导入使用：

| 函数 | 说明 |
|------|------|
| `waitForPageLoad(page)` | 等待页面加载完成 |
| `waitForElement(page, selector)` | 等待元素出现 |
| `tapElement(page, selector)` | 点击元素 |
| `inputText(page, selector, text)` | 输入文本 |
| `switchTab(miniProgram, tabPage)` | 切换 Tab |
| `assertElementExists(page, selector)` | 断言元素存在 |
| `delay(ms)` | 延迟指定毫秒数 |

## 注意事项

1. **微信开发者工具必须保持打开**：测试运行时微信开发者工具需要保持运行状态

2. **测试超时**：E2E 测试默认超时时间为 60 秒，可以在测试套件中调整：

```typescript
describe('测试套件', () => {
  // 设置超时为 120 秒
  beforeAll(async () => {
    // ...
  }, 120000)
})
```

3. **单线程运行**：E2E 测试配置为单线程运行，避免并发冲突

4. **元素选择器**：使用微信小程序的 WXML 元素选择器，如 `.class-name`、`#id`、`tag`

## 调试技巧

1. **截图**：在测试中添加截图帮助调试

```typescript
import { screenshot } from './helpers'

it('测试示例', async () => {
  const page = await miniProgram.currentPage()
  const buffer = await screenshot(page, 'debug-screenshot')
  // 保存到文件
  fs.writeFileSync('debug.png', buffer)
})
```

2. **查看页面数据**：

```typescript
const pageData = await page.data()
console.log(pageData)
```

3. **调用页面方法**：

```typescript
await page.callMethod('methodName', arg1, arg2)
```

## 故障排除

### 测试无法连接到微信开发者工具

1. 确认微信开发者工具已打开
2. 确认服务端口已开启（设置 -> 安全设置）
3. 检查 WECHAT_DEVTOOLS_PATH 环境变量是否正确

### 测试超时

1. 增加测试超时时间
2. 检查小程序是否有网络请求卡住
3. 确认后端服务是否正常运行

### 元素找不到

1. 检查选择器是否正确
2. 使用 `waitForElement` 等待元素出现
3. 确认页面已完全加载
