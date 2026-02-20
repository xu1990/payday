/**
 * 关注、关注流接口 - 与 backend app.api.v1.follow 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/user'

/** 关注/取关响应 */
export interface FollowActionRes {
  ok: boolean
  following: boolean
}

/** 用户项（粉丝/关注列表） */
export interface UserItem {
  id: string
  anonymous_name: string
  avatar: string | null
  bio: string | null
  follower_count: number
  following_count: number
  post_count: number
  allow_follow: number
  allow_comment: number
  status: number
  created_at: string | null
  updated_at: string | null
}

/** 列表响应 */
export interface FollowListRes {
  items: UserItem[]
  total: number
}

/** 关注流帖子项 */
export interface FeedPost {
  id: string
  user_id: string
  anonymous_name: string
  content: string
  images: string[] | null
  tags: string[] | null
  type: string
  salary_range: string | null
  industry: string | null
  city: string | null
  view_count: number
  like_count: number
  comment_count: number
  status: string
  risk_status: string
  risk_score: number | null
  risk_reason: string | null
  created_at: string
  updated_at: string
}

/** 关注流响应 */
export interface FeedRes {
  items: FeedPost[]
  total: number
}

/** 关注用户 */
export function followUser(userId: string) {
  return request<FollowActionRes>({
    url: `${PREFIX}/${userId}/follow`,
    method: 'POST',
  })
}

/** 取关用户 */
export function unfollowUser(userId: string) {
  return request<FollowActionRes>({
    url: `${PREFIX}/${userId}/follow`,
    method: 'DELETE',
  })
}

function queryString(params: Record<string, number | string>): string {
  const queryParts = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
  const q = queryParts.join('&')
  return q ? `?${q}` : ''
}

/** 我的关注流（我关注的人发的帖子） */
export function getMyFeed(params?: { limit?: number; offset?: number }) {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  return request<FeedRes>({
    url: `${PREFIX}/me/feed${queryString({ limit, offset })}`,
    method: 'GET',
  })
}

/** 我的粉丝列表 */
export function getMyFollowers(params?: { limit?: number; offset?: number }) {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  return request<FollowListRes>({
    url: `${PREFIX}/me/followers${queryString({ limit, offset })}`,
    method: 'GET',
  })
}

/** 我的关注列表 */
export function getMyFollowing(params?: { limit?: number; offset?: number }) {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  return request<FollowListRes>({
    url: `${PREFIX}/me/following${queryString({ limit, offset })}`,
    method: 'GET',
  })
}

/** 某用户的粉丝列表（匿名主页用） */
export function getUserFollowers(userId: string, params?: { limit?: number; offset?: number }) {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  return request<FollowListRes>({
    url: `${PREFIX}/${userId}/followers${queryString({ limit, offset })}`,
    method: 'GET',
  })
}

/** 某用户的关注列表 */
export function getUserFollowing(userId: string, params?: { limit?: number; offset?: number }) {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  return request<FollowListRes>({
    url: `${PREFIX}/${userId}/following${queryString({ limit, offset })}`,
    method: 'GET',
  })
}

/** 检查关注状态响应 */
export interface CheckFollowStatusRes {
  is_following: boolean
}

/** 检查是否关注某用户 */
export function checkFollowStatus(userId: string) {
  return request<CheckFollowStatusRes>({
    url: `${PREFIX}/${userId}/follow-status`,
    method: 'GET',
  })
}

/** 批量检查关注状态响应 */
export type BatchFollowStatusRes = Record<string, boolean>

/** 批量检查关注状态 */
export function checkBatchFollowStatus(userIds: string[]): Promise<BatchFollowStatusRes> {
  return request<BatchFollowStatusRes>({
    url: '/api/v1/follows/status',
    method: 'POST',
    data: { user_ids: userIds },
  })
}
