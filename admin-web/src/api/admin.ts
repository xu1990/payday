import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/**
 * CSRF 保护说明：
 *
 * 当前实现使用 JWT + localStorage 存储 token，通过 Authorization header 发送。
 * 这种方式相比 cookie-based 认证已经降低了 CSRF 风险，但仍建议添加额外保护：
 *
 * 1. 后端应验证 Origin/Referer 头，确保请求来自可信来源
 * 2. 敏感操作（如删除、修改）可添加 CSRF token 双重提交验证
 * 3. 考虑实施 SameSite cookie 策略（如果使用 cookie）
 *
 * 如需实现完整的 CSRF token 机制：
 * - 后端在登录响应中返回 csrf_token
 * - 前端存储并在请求头 X-CSRF-Token 中发送
 * - 后端验证该 token 的有效性
 */
export const adminApi = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

adminApi.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  const token = authStore.token
  if (token) config.headers.Authorization = `Bearer ${token}`

  // 为状态变更操作添加 CSRF token
  const csrfToken = authStore.csrfToken
  if (csrfToken && config.method) {
    const method = config.method.toUpperCase()
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }

  return config
})

adminApi.interceptors.response.use(
  (r) => r,
  async (err) => {
    const authStore = useAuthStore()

    // 401错误：尝试刷新token
    if (err.response?.status === 401) {
      // 检查是否有refresh token可用
      if (authStore.refreshToken) {
        try {
          // 尝试刷新token
          const { data } = await adminApi.post<{ access_token: string; csrf_token: string; refresh_token?: string }>(
            '/admin/auth/refresh',
            { refresh_token: authStore.refreshToken }
          )

          // 更新store中的token和csrf token
          authStore.setToken(data.access_token, data.csrf_token, data.refresh_token)

          // 重试原始请求
          if (err.config) {
            err.config.headers.Authorization = `Bearer ${data.access_token}`
            return adminApi(err.config)
          }
        } catch (refreshError) {
          // 刷新失败，退出登录
          console.error('[adminApi] Token refresh failed:', refreshError)
          authStore.logout()
          window.location.href = '/#/login'
        }
      } else {
        // 没有refresh token，直接退出
        authStore.logout()
        window.location.href = '/#/login'
      }
    }

    return Promise.reject(err)
  }
)

export interface LoginReq {
  username: string
  password: string
}

export interface TokenRes {
  access_token: string
  token_type: string
  csrf_token: string
}

export interface AdminUserListItem {
  id: string
  openid: string
  anonymous_name: string
  status: string
  created_at: string | null
}

export interface AdminUserDetail extends AdminUserListItem {
  unionid: string | null
  avatar: string | null
  bio: string | null
  follower_count: number
  following_count: number
  post_count: number
  allow_follow: number
  allow_comment: number
  updated_at: string | null
}

export interface AdminSalaryRecordItem {
  id: string
  user_id: string
  config_id: string
  amount: number
  payday_date: string
  salary_type: string
  risk_status: string
  created_at: string | null
}

export interface AdminStatistics {
  user_total: number
  user_new_today: number
  salary_record_total: number
  salary_record_today: number
}

export function login(data: LoginReq) {
  return adminApi.post<TokenRes>('/admin/auth/login', data)
}

export function getUsers(params: {
  limit?: number
  offset?: number
  keyword?: string
  status?: string
}) {
  return adminApi.get<{ items: AdminUserListItem[]; total: number }>('/admin/users', { params })
}

export function getUser(id: string) {
  return adminApi.get<AdminUserDetail>(`/admin/users/${id}`)
}

export function getSalaryRecords(params: { user_id?: string; limit?: number; offset?: number }) {
  return adminApi.get<{ items: AdminSalaryRecordItem[]; total: number }>('/admin/salary-records', { params })
}

export function deleteSalaryRecord(recordId: string) {
  return adminApi.delete(`/admin/salary-records/${recordId}`)
}

export interface AdminSalaryRecordUpdateRiskRequest {
  risk_status: 'approved' | 'rejected'
}

export function updateSalaryRecordRisk(recordId: string, data: AdminSalaryRecordUpdateRiskRequest) {
  return adminApi.put<AdminSalaryRecordItem>(`/admin/salary-records/${recordId}/risk`, data)
}

export function getStatistics() {
  return adminApi.get<AdminStatistics>('/admin/statistics')
}

// ----- 帖子管理（Sprint 2.4） -----

export interface AdminPostListItem {
  id: string
  user_id: string
  anonymous_name: string
  content: string
  images?: string[] | null
  type: string
  view_count: number
  like_count: number
  comment_count: number
  status: string
  risk_status: string
  risk_score?: number | null
  risk_reason?: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AdminPostUpdateStatusRequest {
  status?: string
  risk_status?: string
  risk_reason?: string
}

export function getPosts(params: {
  status?: string
  risk_status?: string
  limit?: number
  offset?: number
}) {
  return adminApi.get<{ items: AdminPostListItem[]; total: number }>('/admin/posts', { params })
}

export function getPost(id: string) {
  return adminApi.get<AdminPostListItem>(`/admin/posts/${id}`)
}

export function updatePostStatus(id: string, data: AdminPostUpdateStatusRequest) {
  return adminApi.put<{ ok: boolean; id: string }>(`/admin/posts/${id}/status`, data)
}

export function deletePost(id: string) {
  return adminApi.delete(`/admin/posts/${id}`)
}

// ----- 评论管理（Sprint 2.4） -----

export interface AdminCommentListItem {
  id: string
  post_id: string
  user_id: string
  anonymous_name: string
  content: string
  parent_id?: string | null
  like_count: number
  risk_status: string
  created_at: string | null
}

export interface AdminCommentUpdateRiskRequest {
  risk_status: string
  risk_reason?: string
}

export function getComments(params: {
  post_id?: string
  risk_status?: string
  limit?: number
  offset?: number
}) {
  return adminApi.get<{ items: AdminCommentListItem[]; total: number }>('/admin/comments', { params })
}

export function updateCommentRisk(id: string, data: AdminCommentUpdateRiskRequest) {
  return adminApi.put<{ ok: boolean; id: string }>(`/admin/comments/${id}/risk`, data)
}
