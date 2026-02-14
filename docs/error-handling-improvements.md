# 错误处理改进方案

## 当前问题

### 前端问题
1. **管理端**: 有些地方使用 `showError`，有些使用自定义错误处理
2. **小程序端**: 错误处理逻辑分散，不一致
3. **后端**: 缺少请求追踪 ID，调试困难

## 推荐方案

### 1. 后端改进

#### 1.1 添加请求追踪 ID

**实现**:

```python
# app/core/middleware.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 生成唯一的请求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 添加到响应头
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# 在 main.py 中启用
app.add_middleware(RequestTrackingMiddleware)
```

**在日志中使用**:

```python
# 修改异常处理器
async def payday_exception_handler(
    request: Request, exc: PayDayException
) -> JSONResponse:
    request_id = request.state.request_id
    logger.warning(
        f"Business exception: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "code": exc.code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )
    # ...
```

#### 1.2 改进错误日志上下文

```python
# app/core/exceptions.py
def error_response(
    status_code: int,
    message: str,
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """统一错误响应格式"""
    content: Dict[str, Any] = {
        "success": False,
        "message": message,
        "code": code,
    }
    if request_id:
        content["request_id"] = request_id
    if details:
        content["details"] = details

    return JSONResponse(status_code=status_code, content=content)
```

---

### 2. 管理端改进

#### 2.1 创建全局错误处理器

**新建文件**: `admin-web/src/utils/errorHandler.ts`

```typescript
/**
 * 全局错误处理器
 */
import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

export interface ApiError {
  message: string
  code?: string
  details?: unknown
  request_id?: string
  status?: number
}

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK_ERROR',
  AUTHENTICATION = 'AUTHENTICATION_ERROR',
  AUTHORIZATION = 'AUTHORIZATION_ERROR',
  VALIDATION = 'VALIDATION_ERROR',
  SERVER = 'SERVER_ERROR',
  UNKNOWN = 'UNKNOWN_ERROR'
}

/**
 * 从 Axios 错误中提取结构化错误信息
 */
export function parseApiError(error: AxiosError): ApiError {
  if (error.response) {
    const { data, status } = error.response
    return {
      message: (data as ApiError).message || '请求失败',
      code: (data as ApiError).code,
      details: (data as ApiError).details,
      request_id: (data as ApiError).request_id,
      status
    }
  }

  if (error.request) {
    return {
      message: '网络错误，请检查网络连接',
      code: ErrorType.NETWORK
    }
  }

  return {
    message: error.message || '未知错误',
    code: ErrorType.UNKNOWN
  }
}

/**
 * 获取错误类型
 */
export function getErrorType(error: ApiError): ErrorType {
  if (error.status === 401) return ErrorType.AUTHENTICATION
  if (error.status === 403) return ErrorType.AUTHORIZATION
  if (error.status === 422) return ErrorType.VALIDATION
  if (error.status && error.status >= 500) return ErrorType.SERVER
  if (error.code === ErrorType.NETWORK) return ErrorType.NETWORK
  return ErrorType.UNKNOWN
}

/**
 * 显示错误提示
 */
export function showError(error: ApiError, showMessage: boolean = true): void {
  const errorType = getErrorType(error)

  if (!showMessage) return

  switch (errorType) {
    case ErrorType.AUTHENTICATION:
      ElMessage.error({
        message: '登录已过期，请重新登录',
        duration: 3000,
        onClose: () => {
          // 跳转到登录页
          window.location.href = '/login'
        }
      })
      break

    case ErrorType.AUTHORIZATION:
      ElMessage.error({
        message: '没有权限访问此资源',
        duration: 3000
      })
      break

    case ErrorType.VALIDATION:
      ElMessage.warning({
        message: error.message || '请检查输入内容',
        duration: 3000
      })
      break

    case ErrorType.NETWORK:
      ElMessage.error({
        message: '网络连接失败，请检查网络',
        duration: 5000
      })
      break

    case ErrorType.SERVER:
      ElNotification.error({
        title: '服务器错误',
        message: `请求ID: ${error.request_id || 'N/A'}\n${error.message}`,
        duration: 0,
        position: 'top-right'
      })
      break

    default:
      ElMessage.error({
        message: error.message || '操作失败',
        duration: 3000
      })
  }
}

/**
 * 全局错误处理函数
 */
export function handleApiError(
  error: AxiosError | Error,
  options: {
    showMessage?: boolean
    onError?: (error: ApiError) => void
  } = {}
): ApiError {
  const apiError = error instanceof AxiosError
    ? parseApiError(error)
    : { message: error.message, code: ErrorType.UNKNOWN }

  showError(apiError, options.showMessage)

  if (options.onError) {
    options.onError(apiError)
  }

  return apiError
}
```

#### 2.2 在 Axios 拦截器中使用

**修改**: `admin-web/src/api/admin.ts`

```typescript
import { handleApiError, type ApiError } from '@/utils/errorHandler'

// 响应拦截器
adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = handleApiError(error, { showMessage: false })

    // 401 错误特殊处理（token 刷新）
    if (apiError.status === 401 && !error.config._retry) {
      // ... token 刷新逻辑 ...
    }

    return Promise.reject(apiError)
  }
)
```

#### 2.3 在组件中使用

```typescript
import { handleApiError } from '@/utils/errorHandler'
import { ElMessage } from 'element-plus'

async function fetchData() {
  loading.value = true
  try {
    const data = await getUsers(params)
    items.value = data.items
  } catch (error) {
    handleApiError(error, {
      showMessage: true,
      onError: (apiError) => {
        // 自定义错误处理
        console.error('操作失败:', apiError)
        if (apiError.request_id) {
          // 记录 request_id 用于调试
        }
      }
    })
  } finally {
    loading.value = false
  }
}
```

---

### 3. 小程序端改进

#### 3.1 创建统一的错误处理工具

**新建文件**: `miniapp/src/utils/errorHandler.ts`

```typescript
/**
 * 小程序错误处理工具
 */
import type { RequestOptions } from './request'

export interface ApiError {
  message: string
  statusCode?: number
  requestId?: string
}

/**
 * 处理请求错误
 */
export function handleRequestError(
  error: Error | ApiError,
  options: RequestOptions
): ApiError {
  const apiError: ApiError = {
    message: error.message || '请求失败',
    statusCode: (error as ApiError).statusCode,
    requestId: (error as ApiError).requestId
  }

  // 如果不显示错误提示，直接返回
  if (!options.showError) {
    return apiError
  }

  // 使用自定义错误处理
  if (options.errorHandler) {
    const handled = options.errorHandler(error as Error)
    if (handled) {
      return apiError
    }
  }

  // 默认错误处理
  if (error.message.includes('登录已过期')) {
    uni.reLaunch({
      url: '/pages/login/index'
    })
    return apiError
  }

  // 显示错误提示
  uni.showToast({
    title: apiError.message,
    icon: 'none',
    duration: 3000
  })

  return apiError
}
```

#### 3.2 在 request.ts 中集成

**修改**: `miniapp/src/utils/request.ts`

```typescript
import { handleRequestError } from './errorHandler'

export async function request<T = unknown>(
  options: RequestOptions
): Promise<T> {
  // ... 现有代码 ...

  return new Promise((resolve, reject) => {
    uni.request({
      ...rawOptions,
      url,
      header,
      timeout: 30000,
      success: (res) => {
        // ... 现有处理 ...
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          const error = new Error(res.data?.message || '请求失败')
          const apiError = handleRequestError(error, options)
          reject(apiError)
        }
      },
      fail: (err) => {
        const error = new Error(err.errMsg || '网络请求失败')
        const apiError = handleRequestError(error, options)
        reject(apiError)
      },
    })
  })
}
```

---

## 4. 最佳实践

### 4.1 错误日志记录

```typescript
// 前端错误日志
export function logError(error: ApiError, context?: string) {
  const logData = {
    timestamp: new Date().toISOString(),
    error: {
      message: error.message,
      code: error.code,
      status: error.status,
      request_id: error.request_id
    },
    context,
    userAgent: navigator.userAgent,
    url: window.location.href
  }

  // 开发环境打印到控制台
  if (import.meta.env.DEV) {
    console.error('[Error Log]', logData)
  }

  // 生产环境发送到日志服务
  if (!import.meta.env.DEV) {
    sendToLogService(logData)
  }
}
```

### 4.2 错误监控和告警

推荐服务：
1. **Sentry** - 前端和后端都支持
2. **LogRocket** - 前端错误监控和回放
3. **阿里云日志服务** - 国内方案

### 4.3 用户友好的错误消息

| 错误类型 | 用户看到的消息 | 开发者看到的细节 |
|---------|----------------|------------------|
| 网络错误 | "网络连接失败，请检查网络" | 包含请求 ID、完整堆栈 |
| 401 | "登录已过期，请重新登录" | 包含 token、用户 ID |
| 403 | "没有权限访问此资源" | 包含所需权限、当前权限 |
| 422 | "请检查输入内容" | 包含验证错误的字段 |
| 500 | "服务器错误，请稍后重试" | 包含请求 ID、错误堆栈 |

---

## 实施步骤

### 第一阶段（立即）
1. ✅ 后端添加请求追踪 ID
2. ✅ 创建统一错误处理工具
3. ✅ 在关键 API 调用中使用新错误处理

### 第二阶段（2周内）
1. 在所有组件中迁移到新错误处理
2. 添加错误日志收集
3. 实施错误监控服务

### 第三阶段（1个月内）
1. 分析错误日志找出高频问题
2. 优化错误消息
3. 实施自动化告警

---

**文档版本**: 1.0
**最后更新**: 2026-02-14
**状态**: 待实施
