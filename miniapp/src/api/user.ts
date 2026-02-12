/**
 * 用户相关 API - 与 backend /api/v1/user 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/user'

export interface UserInfo {
  id: string
  anonymous_name: string
  avatar: string | null
  bio: string | null
  follower_count: number
  following_count: number
  post_count: number
  allow_follow: number
  allow_comment: number
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface UserUpdateParams {
  anonymous_name?: string
  avatar?: string
  bio?: string
  allow_follow?: number
  allow_comment?: number
}

export interface UserProfileData {
  user: {
    id: string
    anonymous_name: string
    avatar: string | null
    bio: string | null
    follower_count: number
    following_count: number
    post_count: number
    is_following: boolean
  }
  posts: Array<{
    id: string
    content: string
    images: string[] | null
    type: string
    like_count: number
    comment_count: number
    created_at: string
  }>
  checkins: Array<{
    id: string
    mood: string
    checkin_date: string
    created_at: string
  }>
}

/**
 * 获取当前登录用户信息
 */
export function getCurrentUser(): Promise<UserInfo> {
  return request<UserInfo>({ url: `${PREFIX}/me`, method: 'GET' })
}

/**
 * 更新当前用户信息
 */
export function updateCurrentUser(data: UserUpdateParams): Promise<UserInfo> {
  return request<UserInfo>({
    url: `${PREFIX}/me`,
    method: 'PUT',
    data,
  })
}

/**
 * 获取用户主页数据（包含帖子、打卡记录等）
 */
export function getUserProfile(targetUserId: string): Promise<UserProfileData> {
  return request<UserProfileData>({
    url: `${PREFIX}/profile-data/${targetUserId}`,
    method: 'GET',
  })
}

// ==================== 关注相关 ====================

export interface FollowActionRes {
  ok: boolean
  following: boolean
}

export interface FollowListRes {
  items: UserInfo[]
  total: number
}

/**
 * 关注用户
 */
export function followUser(targetUserId: string): Promise<FollowActionRes> {
  return request<FollowActionRes>({
    url: `${PREFIX}/${targetUserId}/follow`,
    method: 'POST',
  })
}

/**
 * 取关用户
 */
export function unfollowUser(targetUserId: string): Promise<FollowActionRes> {
  return request<FollowActionRes>({
    url: `${PREFIX}/${targetUserId}/follow`,
    method: 'DELETE',
  })
}

/**
 * 获取我的粉丝列表
 */
export function getMyFollowers(params?: { limit?: number; offset?: number }): Promise<FollowListRes> {
  const { limit = 20, offset = 0 } = params || {}
  return request<FollowListRes>({
    url: `${PREFIX}/me/followers?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

/**
 * 获取我的关注列表
 */
export function getMyFollowing(params?: { limit?: number; offset?: number }): Promise<FollowListRes> {
  const { limit = 20, offset = 0 } = params || {}
  return request<FollowListRes>({
    url: `${PREFIX}/me/following?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

/**
 * 获取用户粉丝列表
 */
export function getUserFollowers(targetUserId: string, params?: { limit?: number; offset?: number }): Promise<FollowListRes> {
  const { limit = 20, offset = 0 } = params || {}
  return request<FollowListRes>({
    url: `${PREFIX}/${targetUserId}/followers?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

/**
 * 获取用户关注列表
 */
export function getUserFollowing(targetUserId: string, params?: { limit?: number; offset?: number }): Promise<FollowListRes> {
  const { limit = 20, offset = 0 } = params || {}
  return request<FollowListRes>({
    url: `${PREFIX}/${targetUserId}/following?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

export default {
  getCurrentUser,
  updateCurrentUser,
  getUserProfile,
  // 关注相关
  followUser,
  unfollowUser,
  getMyFollowers,
  getMyFollowing,
  getUserFollowers,
  getUserFollowing,
}
