import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const adminApi = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

adminApi.interceptors.request.use((config) => {
  const token = useAuthStore().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

adminApi.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore().logout()
      window.location.href = '/#/login'
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
