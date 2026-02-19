# PayDay Miniapp

薪日 PayDay 微信小程序 - 基于 uni-app + Vue3 构建的社交娱乐小程序。

## 技术栈

- **框架**: uni-app (Vue 3)
- **构建工具**: Vite
- **语言**: TypeScript
- **状态管理**: Pinia
- **UI 组件**: @dcloudio/uni-ui
- **HTTP**: 自定义封装 (基于 uni.request)
- **测试**: Vitest

## 项目结构

```
miniapp/
├── src/
│   ├── api/                # API 请求模块
│   │   ├── auth.ts         # 认证
│   │   ├── user.ts         # 用户
│   │   ├── payday.ts       # 薪日
│   │   ├── salary.ts       # 薪资
│   │   ├── post.ts         # 帖子
│   │   ├── comment.ts      # 评论
│   │   ├── like.ts         # 点赞
│   │   ├── follow.ts       # 关注
│   │   ├── notification.ts # 通知
│   │   ├── theme.ts        # 主题
│   │   ├── membership.ts   # 会员
│   │   └── payment.ts      # 支付
│   ├── components/         # 公共组件
│   │   ├── LazyImage.vue   # 懒加载图片
│   │   ├── Loading.vue     # 加载状态
│   │   ├── EmptyState.vue  # 空状态
│   │   ├── AppLogos.vue    # Logo 组件
│   │   ├── InputEntry.vue  # 输入框组件
│   │   └── AppFooter.vue   # 底部导航
│   ├── pages/              # 页面
│   │   ├── index.vue       # 首页
│   │   ├── login.vue       # 登录
│   │   ├── square.vue      # 广场
│   │   ├── feed.vue        # 动态
│   │   ├── post-create.vue # 发帖
│   │   ├── post-detail.vue # 帖子详情
│   │   ├── payday-setting/ # 薪日设置
│   │   ├── salary-record/  # 薪资记录
│   │   ├── statistics/     # 统计
│   │   ├── poster/         # 海报
│   │   ├── profile/        # 个人资料
│   │   ├── themes/         # 主题
│   │   ├── checkin/        # 签到
│   │   ├── insights/       # 洞察
│   │   ├── membership/     # 会员
│   │   ├── orders/         # 订单
│   │   ├── settings/       # 设置
│   │   ├── search/         # 搜索
│   │   ├── user-home/      # 用户主页
│   │   ├── followers/      # 粉丝/关注
│   │   └── notification/   # 通知
│   ├── services/           # 业务服务层
│   │   ├── AuthService.ts  # 认证服务
│   │   ├── UserService.ts  # 用户服务
│   │   ├── SalaryService.ts # 薪资服务
│   │   ├── PostService.ts  # 帖子服务
│   │   ├── NotificationService.ts # 通知服务
│   │   └── CheckinService.ts # 签到服务
│   ├── stores/             # Pinia 状态管理
│   │   ├── auth.ts         # 认证状态
│   │   ├── user.ts         # 用户状态
│   │   ├── notification.ts # 通知状态
│   │   └── post.ts         # 帖子状态
│   ├── utils/              # 工具函数
│   │   ├── request.ts      # HTTP 请求封装
│   │   ├── format.ts       # 格式化
│   │   ├── crypto.ts       # 加密
│   │   ├── toast.ts        # 提示
│   │   ├── error.ts        # 错误处理
│   │   ├── sanitize.ts     # 内容净化
│   │   └── performance.ts  # 性能优化
│   ├── composables/        # 组合式 API
│   │   ├── useRequest.ts   # 请求 Hook
│   │   ├── useDebounce.ts  # 防抖
│   │   ├── usePagination.ts # 分页
│   │   └── useErrorHandler.ts # 错误处理
│   ├── constants/          # 常量
│   │   └── validation.ts   # 验证规则
│   ├── App.vue             # 应用入口
│   ├── main.ts             # 主入口
│   └── pages.json          # 页面配置
├── tests/                  # 测试
├── package.json
└── vite.config.ts
```

## 快速开始

### 环境要求

- Node.js 16+
- npm 或 pnpm
- 微信开发者工具

### 安装依赖

```bash
npm install
```

### 开发

```bash
npm run dev
```

使用微信开发者工具打开 `dist/dev/mp-weixin` 目录。

### 构建

```bash
npm run build
```

### 类型检查

```bash
npm run type-check
```

### 测试

```bash
# 运行测试
npm run test

# Vitest UI (交互式)
npm run test:ui

# 覆盖率
npm run test:coverage
```

### 代码规范

```bash
# Lint (从根目录运行)
cd .. && npm run lint:miniapp    # ESLint

# Format (从根目录运行)
cd .. && npm run format:miniapp  # Prettier
```

## 核心功能模块

### 1. 认证模块

使用微信 code2session 登录，JWT Token 存储：

```typescript
// src/stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>('')
  const isLoggedIn = computed(() => !!token.value)

  async function login() {
    const res = await uni.login({ provider: 'weixin' })
    const { access_token } = await authService.wechatLogin(res.code)
    token.value = access_token
  }

  return { token, isLoggedIn, login }
})
```

### 2. 薪日管理

用户设置发薪日，系统计算倒计时：

```typescript
// src/pages/payday-setting/index.vue
import { usePaydayStore } from '@/stores/payday'

const paydayStore = usePaydayStore()
await paydayStore.setPayday(15) // 每月15号
```

### 3. 薪资记录

加密存储薪资数据：

```typescript
// src/services/SalaryService.ts
async createSalary(amount: number, mood: string) {
  return await salaryApi.create({
    amount: encryptAmount(amount), // 客户端加密
    mood
  })
}
```

### 4. 社区功能

发布帖子、评论、点赞、关注：

```typescript
// src/services/PostService.ts
class PostService {
  async createPost(content: string, images: string[]) {
    return await postApi.create({ content, images })
  }

  async getPosts(page: number, pageSize: number) {
    return await postApi.list({ page, page_size: pageSize })
  }
}
```

### 5. 会员购买

微信支付购买会员：

```typescript
// src/api/payment.ts
export async function createMembershipOrder(membershipId: number) {
  const res = await request<{
    prepay_id: string
    sign_info: WechatPaySignInfo
  }>('/payment/wechat/create', {
    method: 'POST',
    data: { membership_id: membershipId }
  })

  // 调起微信支付
  await uni.requestPayment({
    provider: 'wxpay',
    ...res.sign_info
  })
}
```

## HTTP 请求封装

基于 `uni.request` 封装，支持：

- 自动 Token 注入
- 请求/响应拦截
- 错误统一处理
- 加密数据传输

```typescript
// src/utils/request.ts
export function request<T>(options: RequestOptions): Promise<T> {
  const authStore = useAuthStore()

  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      header: {
        Authorization: `Bearer ${authStore.token}`,
        ...options.header
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          handleError(res)
          reject(res)
        }
      },
      fail: reject
    })
  })
}
```

## 组合式 API (Composables)

### useRequest

统一的请求状态管理：

```vue
<script setup lang="ts">
import { useRequest } from '@/composables/useRequest'
import { getUserInfo } from '@/api/user'

const { data, loading, error, execute } = useRequest(getUserInfo)

onMounted(() => execute())
</script>
```

### usePagination

分页加载：

```vue
<script setup lang="ts">
import { usePagination } from '@/composables/usePagination'
import { getPosts } from '@/api/post'

const { list, loading, hasMore, loadMore, reset } = usePagination(getPosts)

onReachBottom(() => {
  if (hasMore.value) loadMore()
})
</script>
```

### useDebounce

防抖处理：

```vue
<script setup lang="ts">
import { useDebounce } from '@/composables/useDebounce'

const keyword = ref('')
const { debouncedValue } = useDebounce(keyword, 300)

watch(debouncedValue, (val) => {
  // 执行搜索
})
</script>
```

## 公共组件

### LazyImage

懒加载图片组件，支持占位符和加载状态：

```vue
<LazyImage
  :src="imageUrl"
  :width="300"
  :height="200"
  placeholder="/static/placeholder.png"
  mode="aspectFill"
/>
```

### EmptyState

空状态展示：

```vue
<EmptyState
  icon="inbox"
  title="暂无内容"
  description="快去发第一条动态吧"
/>
```

### Loading

加载状态：

```vue
<Loading
  :loading="isLoading"
  text="加载中..."
/>
```

## 状态管理 (Pinia)

### Auth Store

```typescript
// src/stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(uni.getStorageSync('token') || '')
  const userInfo = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    uni.setStorageSync('token', newToken)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    uni.removeStorageSync('token')
  }

  return { token, userInfo, isLoggedIn, setToken, logout }
})
```

### Notification Store

未读消息计数：

```typescript
// src/stores/notification.ts
export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)

  async function fetchUnreadCount() {
    const res = await notificationApi.getUnreadCount()
    unreadCount.value = res.count
  }

  return { unreadCount, fetchUnreadCount }
})
```

## 工具函数

### 格式化

```typescript
// src/utils/format.ts

// 格式化金额
export function formatAmount(amount: number): string {
  return (amount / 100).toFixed(2)
}

// 格式化日期
export function formatDate(date: Date): string {
  return dayjs(date).format('YYYY-MM-DD')
}

// 薪日倒计时
export function getPaydayCountdown(payday: number): number {
  const today = dayjs().date()
  const target = payday >= today ? payday : payday + 32
  return dayjs().date(target).diff(dayjs(), 'day')
}
```

### 加密

```typescript
// src/utils/crypto.ts

// 薪资金额加密 (与后端对应)
export function encryptAmount(amount: number): string {
  // 加密逻辑
}

// 敏感信息脱敏
export function maskPhone(phone: string): string {
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}
```

### 内容净化

```typescript
// src/utils/sanitize.ts

// XSS 防护
export function sanitizeHtml(html: string): string {
  // 移除危险标签
}

// 敏感词过滤
export function filterSensitiveWords(text: string): string {
  // 替换敏感词
}
```

## 性能优化

### 图片优化

- 使用 LazyImage 组件懒加载
- 图片 CDN 加速
- WebP 格式支持

### 列表优化

- 虚拟列表 (长列表)
- 分页加载
- 骨架屏占位

### 缓存策略

- 用户信息本地缓存
- API 响应缓存
- 静态资源缓存

## 错误处理

统一的错误处理机制：

```typescript
// src/utils/error.ts
export function handleError(error: any) {
  console.error('Error:', error)

  if (error.statusCode === 401) {
    // Token 过期，重新登录
    const authStore = useAuthStore()
    authStore.logout()
    uni.navigateTo({ url: '/pages/login/index' })
  } else if (error.statusCode === 403) {
    uni.showToast({ title: '无权限操作', icon: 'none' })
  } else {
    uni.showToast({ title: error.message || '请求失败', icon: 'none' })
  }
}
```

## 页面配置

页面路由配置在 `pages.json`：

```json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "薪日"
      }
    },
    {
      "path": "pages/square/index",
      "style": {
        "navigationBarTitleText": "广场"
      }
    }
  ],
  "tabBar": {
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png"
      }
    ]
  }
}
```

## 开发建议

### 组件开发

- 使用 Composition API
- Props 定义类型
- 使用 `defineEmits` 定义事件
- 避免过度组件化

### 状态管理

- 跨页面状态用 Pinia
- 页面内状态用 `ref`/`reactive`
- 持久化状态用 `uni.setStorageSync`

### 性能建议

- 避免大量数据渲染
- 图片使用 CDN
- 减少 setData 频率
- 使用防抖/节流

## 测试

```bash
# 运行所有测试
npm run test

# 运行特定测试文件
npm run test -- src/utils/format.test.ts

# 覆盖率报告
npm run test:coverage
```

## 常见问题

### 微信登录失败

- 检查 `appid` 配置
- 确认小程序已开通登录权限
- 检查后端接口返回

### 图片上传失败

- 检查 COS 配置
- 确认图片大小限制
- 检查网络状态

### 支付调起失败

- 检查支付参数
- 确认商户配置
- 测试环境无法测试真实支付

## 发布流程

1. 配置小程序 AppID
2. 运行 `npm run build`
3. 微信开发者工具上传代码
4. 提交审核
5. 发布上线

## 资源链接

- [uni-app 文档](https://uniapp.dcloud.net.cn/)
- [Vue 3 文档](https://cn.vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [微信小程序文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
