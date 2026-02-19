# PayDay Admin Web

薪日 PayDay 管理后台 - 基于 Vue3 + Element Plus 构建的 Web 管理系统。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **UI 库**: Element Plus
- **构建工具**: Vite
- **语言**: TypeScript
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP**: Axios
- **测试**: Vitest
- **组件文档**: Storybook

## 项目结构

```
admin-web/
├── src/
│   ├── api/                # API 请求模块
│   │   ├── admin.ts        # 管理员
│   │   ├── membership.ts   # 会员配置
│   │   ├── theme.ts        # 主题管理
│   │   ├── order.ts        # 订单管理
│   │   └── topics.ts       # 话题管理
│   ├── components/         # 公共组件
│   │   ├── BaseDataTable.vue    # 数据表格
│   │   ├── BaseFormDialog.vue   # 表单弹窗
│   │   ├── ActionButtons.vue    # 操作按钮
│   │   ├── StatusTag.vue        # 状态标签
│   │   ├── SearchToolbar.vue    # 搜索栏
│   │   └── *.stories.vue        # Storybook 故事
│   ├── views/              # 页面视图
│   │   ├── Login.vue       # 登录
│   │   ├── Layout.vue      # 布局
│   │   ├── UserList.vue    # 用户列表
│   │   ├── UserDetail.vue  # 用户详情
│   │   ├── PostList.vue    # 帖子列表
│   │   ├── CommentList.vue # 评论列表
│   │   ├── RiskPending.vue # 风控审核
│   │   ├── Statistics.vue  # 统计
│   │   ├── Theme.vue       # 主题管理
│   │   ├── Membership.vue  # 会员配置
│   │   ├── Order.vue       # 订单管理
│   │   └── topics/         # 话题管理
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── stores/             # Pinia 状态管理
│   │   └── auth.ts         # 认证状态
│   ├── composables/        # 组合式 API
│   │   ├── usePagination.ts       # 分页
│   │   ├── useErrorHandler.ts     # 错误处理
│   │   ├── useAbortableRequest.ts # 可中断请求
│   │   └── useRiskManagement.ts   # 风控管理
│   ├── utils/              # 工具函数
│   │   ├── request.ts      # HTTP 请求
│   │   ├── format.ts       # 格式化
│   │   ├── validation.ts   # 验证
│   │   ├── error.ts        # 错误处理
│   │   ├── debounce.ts     # 防抖
│   │   └── performance.ts  # 性能
│   ├── constants/          # 常量
│   │   └── status.ts       # 状态常量
│   ├── types/              # 类型定义
│   │   └── api.ts          # API 类型
│   ├── App.vue             # 应用入口
│   └── main.ts             # 主入口
├── tests/                  # 测试
├── .storybook/             # Storybook 配置
├── package.json
└── vite.config.ts
```

## 快速开始

### 环境要求

- Node.js 16+
- npm 或 pnpm

### 安装依赖

```bash
npm install
```

### 开发

```bash
npm run dev
```

访问 http://localhost:5174

开发服务器会自动将 `/api` 代理到 `http://127.0.0.1:8000`。

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

### Storybook

```bash
# 启动 Storybook
npm run storybook

# 构建 Storybook
npm run build-storybook
```

### 代码规范

```bash
# Lint (从根目录运行)
cd .. && npm run lint:admin    # ESLint

# Format (从根目录运行)
cd .. && npm run format:admin  # Prettier
```

## 核心功能模块

### 1. 认证模块

管理员登录认证：

```typescript
// src/stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('admin_token') || '')
  const userInfo = ref<AdminUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const { access_token } = await adminApi.login({ username, password })
    token.value = access_token
    localStorage.setItem('admin_token', access_token)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, userInfo, isLoggedIn, login, logout }
})
```

### 2. 用户管理

查看用户列表、详情、状态：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { getUserList } from '@/api/admin'
import { usePagination } from '@/composables/usePagination'

const {
  loading,
  data: users,
  pagination,
  fetchData
} = usePagination(getUserList)

onMounted(() => fetchData())
</script>

<template>
  <BaseDataTable
    :data="users"
    :loading="loading"
    :pagination="pagination"
    @page-change="fetchData"
  />
</template>
```

### 3. 内容审核

审核用户发布的帖子和评论：

```vue
<script setup lang="ts">
import { useRiskManagement } from '@/composables/useRiskManagement'

const { approvePost, rejectPost } = useRiskManagement()

async function handleApprove(postId: number) {
  await approvePost(postId)
  ElMessage.success('审核通过')
}
</script>
```

### 4. 统计分析

查看平台数据统计：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getStatistics } from '@/api/admin'

const stats = ref({
  userCount: 0,
  postCount: 0,
  salaryCount: 0,
  activeUsers: 0
})

onMounted(async () => {
  stats.value = await getStatistics()
})
</script>
```

### 5. 配置管理

管理会员配置、主题配置等：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { getMembershipConfig, updateMembershipConfig } from '@/api/membership'

const config = ref<MembershipConfig>({})

async function loadConfig() {
  config.value = await getMembershipConfig()
}

async function saveConfig() {
  await updateMembershipConfig(config.value)
  ElMessage.success('保存成功')
}
</script>
```

## 公共组件

### BaseDataTable

通用数据表格组件：

```vue
<BaseDataTable
  :data="tableData"
  :columns="columns"
  :loading="loading"
  :pagination="pagination"
  @selection-change="handleSelectionChange"
  @page-change="handlePageChange"
>
  <template #actions="{ row }">
    <ActionButtons
      :row="row"
      :actions="['view', 'edit', 'delete']"
      @view="handleView"
      @edit="handleEdit"
      @delete="handleDelete"
    />
  </template>
</BaseDataTable>
```

### BaseFormDialog

表单弹窗组件：

```vue
<BaseFormDialog
  v-model="dialogVisible"
  :title="dialogTitle"
  :form="formData"
  :rules="formRules"
  @confirm="handleConfirm"
>
  <el-form-item label="用户名" prop="username">
    <el-input v-model="formData.username" />
  </el-form-item>
</BaseFormDialog>
```

### StatusTag

状态标签：

```vue
<StatusTag :status="user.status" />
<!-- active: 绿色, inactive: 灰色, banned: 红色 -->
```

### ActionButtons

操作按钮组：

```vue
<ActionButtons
  :row="dataRow"
  :actions="['view', 'edit', 'delete']"
  @view="handleView"
  @edit="handleEdit"
  @delete="handleDelete"
/>
```

### SearchToolbar

搜索工具栏：

```vue
<SearchToolbar
  v-model="searchForm"
  :fields="searchFields"
  @search="handleSearch"
  @reset="handleReset"
/>
```

## 组合式 API (Composables)

### usePagination

分页管理：

```typescript
import { usePagination } from '@/composables/usePagination'
import { getUserList } from '@/api/admin'

const {
  loading,
  data,
  pagination,
  fetchData
} = usePagination(getUserList, {
  defaultPageSize: 20
})

// 刷新数据
await fetchData()
```

### useErrorHandler

统一错误处理：

```typescript
import { useErrorHandler } from '@/composables/useErrorHandler'

const { handleError } = useErrorHandler()

try {
  await someApi()
} catch (error) {
  handleError(error) // 自动显示错误提示
}
```

### useAbortableRequest

可中断的请求（防止组件卸载后更新状态）：

```typescript
import { useAbortableRequest } from '@/composables/useAbortableRequest'

const { request, abort } = useAbortableRequest()

const data = await request(getUserList)

// 组件卸载时自动中断请求
onUnmounted(() => abort())
```

### useRiskManagement

风控管理：

```typescript
import { useRiskManagement } from '@/composables/useRiskManagement'

const {
  approvePost,
  rejectPost,
  approveComment,
  rejectComment
} = useRiskManagement()

await approvePost(postId, { reason: '审核通过' })
await rejectPost(postId, { reason: '包含违规内容' })
```

## 路由配置

路由定义在 `src/router/index.ts`：

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/UserList.vue')
      },
      {
        path: 'posts',
        name: 'PostList',
        component: () => import('@/views/PostList.vue')
      },
      // ...
    ]
  }
]
```

路由守卫实现认证检查：

```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})
```

## API 请求封装

基于 Axios 封装，支持：

- 自动 Token 注入
- 请求/响应拦截
- 错误统一处理
- 请求取消

```typescript
// src/utils/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 请求拦截
service.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截
service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    } else {
      ElMessage.error(error.response?.data?.message || '请求失败')
    }
    return Promise.reject(error)
  }
)
```

## 状态管理 (Pinia)

### Auth Store

```typescript
// src/stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('admin_token') || '')
  const userInfo = ref<AdminUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const { access_token, admin } = await adminApi.login({ username, password })
    token.value = access_token
    userInfo.value = admin
    localStorage.setItem('admin_token', access_token)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, userInfo, isLoggedIn, login, logout }
})
```

## 工具函数

### 格式化

```typescript
// src/utils/format.ts

// 格式化日期
export function formatDate(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化金额
export function formatAmount(amount: number): string {
  return `¥ ${(amount / 100).toFixed(2)}`
}

// 手机号脱敏
export function maskPhone(phone: string): string {
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}
```

### 验证

```typescript
// src/utils/validation.ts

// 验证手机号
export function isValidPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone)
}

// 验证邮箱
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}
```

## Storybook 组件文档

使用 Storybook 为组件编写文档：

```vue
<!-- src/components/StatusTag.stories.vue -->
<script setup lang="ts">
import StatusTag from './StatusTag.vue'

export default {
  title: 'Components/StatusTag',
  component: StatusTag
}

export const Active = {
  args: {
    status: 'active'
  }
}

export const Inactive = {
  args: {
    status: 'inactive'
  }
}
</script>

<template>
  <Story title="Active">
    <StatusTag status="active" />
  </Story>
</template>
```

运行 Storybook：

```bash
npm run storybook
```

访问 http://localhost:6006

## 性能优化

### 路由懒加载

```typescript
const routes = [
  {
    path: '/users',
    component: () => import('@/views/UserList.vue')
  }
]
```

### 请求优化

- 防抖搜索
- 请求取消
- 数据缓存

### 渲染优化

- 虚拟列表（大数据量）
- 分页加载
- 懒加载组件

## 开发建议

### 组件开发

- 使用 Composition API
- Props 定义类型
- 使用 `defineEmits` 定义事件
- 可复用组件放到 `components/`

### 样式规范

- 优先使用 Element Plus 组件
- 使用 SCSS 编写样式
- 避免内联样式

### 代码规范

- 使用 TypeScript 类型
- 避免使用 `any`
- 函数添加 JSDoc 注释

## 常见问题

### 登录后刷新页面丢失登录状态

- 检查 Token 是否正确存储到 localStorage
- 检查路由守卫是否正确读取 Token

### API 请求 401 错误

- 检查 Token 是否过期
- 检查 Authorization 请求头格式

### 表格分页不工作

- 检查 pagination 参数是否正确传递
- 检查 @page-change 事件是否正确绑定

## 环境变量

开发环境 API 代理配置在 `vite.config.ts`：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
```

生产环境需要配置 Nginx 反向代理：

```nginx
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 部署

### 构建

```bash
npm run build
```

输出目录：`dist/`

### Nginx 配置

```nginx
server {
    listen 80;
    server_name admin.payday.com;

    root /var/www/payday/admin-web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
    }
}
```

## 资源链接

- [Vue 3 文档](https://cn.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vite 文档](https://cn.vitejs.dev/)
- [Storybook 文档](https://storybook.js.org/)
