import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/**
 * CSRF 保护说明：
 *
 * 当前实现：后端设置httpOnly cookie，前端通过localStorage存储CSRF token
 * 请求时在X-CSRF-Token header中发送CSRF token
 *
 * 改进方案：添加token刷新队列机制，防止并发刷新请求冲突
 */

/**
 * 检测是否有请求正在刷新token
 */
let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null
// 存储等待重试的请求
let failedQueue: Array<(token: string) => void> = []
// 刷新重试计数器，防止无限重试
let refreshRetryCount = 0
const MAX_REFRESH_RETRIES = 3

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    try {
      prom(error || token)
    } catch (err) {
      console.error('[adminApi] Error processing queue item:', err)
    }
  })
  failedQueue = []
}

const adminApi = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// 请求拦截器：添加token
adminApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    console.log('[adminApi Request]', config.method?.toUpperCase(), config.url, 'token:', authStore.token ? `${authStore.token.substring(0, 20)}...` : 'MISSING')

    // 添加 JWT token 到 Authorization header
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // 添加 CSRF token 到请求头（用于状态变更操作）
    if (authStore.csrfToken) {
      config.headers['X-CSRF-Token'] = authStore.csrfToken
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：自动解包统一响应格式 + 处理401错误
adminApi.interceptors.response.use(
  (response) => {
    // 自动解包统一响应格式 {code, message, details}
    const data = response.data
    if (data && typeof data === 'object' && 'code' in data && 'details' in data) {
      // 统一格式响应，直接提取 details
      response.data = data.details
    }
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    // 对于非401错误，直接返回（不触发token刷新）
    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }

    // 以下是401错误的处理逻辑
    // 如果已经重试过，直接拒绝
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    // 检查重试次数，防止无限重试
    if (refreshRetryCount >= MAX_REFRESH_RETRIES) {
      console.error('[adminApi] Max refresh retries reached')
      authStore.logout()
      return Promise.reject(error)
    }

    // 如果正在刷新，将请求加入队列
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          resolve(adminApi(originalRequest))
        })
      }).catch(err => {
        return Promise.reject(err)
      })
    }

    originalRequest._retry = true
    isRefreshing = true
    refreshRetryCount++

    // 开始刷新token
    refreshPromise = (async () => {
      try {
        const refreshToken = authStore.refreshToken

        // SECURITY: 管理端不需要user_id进行token刷新
        // 后端可以从refresh token中解析admin信息
        const { data } = await adminApi.post('/admin/auth/refresh', {
          refresh_token: refreshToken
        })

        // 更新token
        authStore.setToken(data.access_token, data.csrf_token, data.refresh_token)

        // 处理队列中的请求
        processQueue(null, data.access_token)

        // 重置重试计数器
        refreshRetryCount = 0
        isRefreshing = false
        return true
      } catch (refreshError) {
        console.error('[adminApi] Token refresh failed:', refreshError)

        // 刷新失败，清除token并处理队列
        processQueue(refreshError, null)
        authStore.logout()

        // 重置状态
        refreshRetryCount = 0
        isRefreshing = false
        return false
      }
    })()

    try {
      const refreshed = await refreshPromise
      if (refreshed) {
        // 重试原始请求
        const newToken = authStore.token
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return adminApi(originalRequest)
      }
    } catch (retryError) {
      return Promise.reject(retryError)
    }

    return Promise.reject(error)
  }
)

export default adminApi

// ==================== 认证 ====================

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  csrf_token: string
  admin: {
    id: number
    username: string
  }
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const res = await adminApi.post<LoginResponse>('/admin/auth/login', data)
  return res.data
}

// ==================== 用户管理 ====================

export interface AdminUserListItem {
  id: number
  openid: string
  nickname: string
  avatar_url: string
  status: string
  created_at: string
  post_count: number
  follower_count: number
  following_count: number
}

export interface AdminUserDetail extends AdminUserListItem {
  phone?: string
  email?: string
  bio?: string
  salary_count: number
  last_login_at?: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
}

export async function getUsers(params?: UserListParams): Promise<{
  items: AdminUserListItem[]
  total: number
}> {
  const res = await adminApi.get('/admin/users', { params })
  return res.data
}

export async function getUser(userId: number): Promise<AdminUserDetail> {
  const res = await adminApi.get(`/admin/users/${userId}`)
  return res.data
}

// ==================== 帖子管理 ====================

export interface AdminPostListItem {
  id: number
  user_id: number
  user_nickname: string
  user_avatar: string
  content: string
  images: string[]
  topic_id?: number
  topic_name?: string
  status: string
  created_at: string
  like_count: number
  comment_count: number
  risk_status?: string
}

export interface PostListParams {
  page?: number
  page_size?: number
  status?: string
  risk_status?: string
  user_id?: number
  topic_id?: number
  keyword?: string
}

export async function getPosts(params?: PostListParams): Promise<{
  items: AdminPostListItem[]
  total: number
}> {
  const res = await adminApi.get('/admin/posts', { params })
  return res.data
}

export async function getPost(postId: number): Promise<AdminPostListItem> {
  const res = await adminApi.get(`/admin/posts/${postId}`)
  return res.data
}

export async function updatePostStatus(
  postId: number,
  data: {
    status?: string  // normal | hidden | deleted
    risk_status?: string  // approved | rejected
    risk_reason?: string
  }
): Promise<void> {
  await adminApi.put(`/admin/posts/${postId}/status`, data)
}

export async function deletePost(postId: number): Promise<void> {
  await adminApi.delete(`/admin/posts/${postId}`)
}

// ==================== 评论管理 ====================

export interface AdminCommentListItem {
  id: number
  post_id: number
  user_id: number
  user_nickname: string
  user_avatar: string
  content: string
  status: string
  created_at: string
  risk_status?: string
}

export interface CommentListParams {
  page?: number
  page_size?: number
  post_id?: number
  user_id?: number
  status?: string
  risk_status?: string
}

export async function getComments(params?: CommentListParams): Promise<{
  items: AdminCommentListItem[]
  total: number
}> {
  const res = await adminApi.get('/admin/comments', { params })
  return res.data
}

export async function updateCommentRisk(
  commentId: number,
  data: {
    risk_status: string  // approved | rejected
    risk_reason?: string
  }
): Promise<void> {
  await adminApi.put(`/admin/comments/${commentId}/risk`, data)
}

// ==================== 薪资记录 ====================

export interface AdminSalaryRecord {
  id: number
  user_id: number
  user_nickname: string
  amount: number
  mood: string
  created_at: string
  risk_status?: string
}

export interface SalaryListParams {
  page?: number
  page_size?: number
  user_id?: number
  risk_status?: string
}

export async function getSalaryRecords(
  params?: SalaryListParams
): Promise<{
  items: AdminSalaryRecord[]
  total: number
}> {
  const res = await adminApi.get('/admin/salary-records', { params })
  return res.data
}

export async function deleteSalaryRecord(recordId: number): Promise<void> {
  await adminApi.delete(`/admin/salary-records/${recordId}`)
}

export async function updateSalaryRecordRisk(
  recordId: number,
  data: {
    risk_status: string  // approved | rejected
    risk_reason?: string
  }
): Promise<void> {
  await adminApi.put(`/admin/salary-records/${recordId}/risk`, data)
}

// ==================== 统计 ====================

export interface AdminStatistics {
  user_count: number
  post_count: number
  comment_count: number
  salary_count: number
  active_users_today: number
  new_users_today: number
  posts_today: number
}

export async function getStatistics(): Promise<AdminStatistics> {
  const res = await adminApi.get('/admin/statistics')
  return res.data
}