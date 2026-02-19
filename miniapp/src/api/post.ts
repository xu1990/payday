/**
 * 帖子 - 与 backend /api/v1/posts 一致
 */
import request, { type RequestOptions } from '@/utils/request'

const PREFIX = '/api/v1/posts'

export type PostType = 'complaint' | 'sharing' | 'question'

export interface PostItem {
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

export interface PostCreateParams {
  content: string
  images?: string[] | null
  tags?: string[] | null
  type?: PostType
  salary_range?: string | null
  industry?: string | null
  city?: string | null
}

function queryString(params: Record<string, string | number>): string {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => s.set(k, String(v)))
  const q = s.toString()
  return q ? `?${q}` : ''
}

/** 帖子列表（广场：热门/最新） */
export function getPostList(params: { sort: 'hot' | 'latest'; limit?: number; offset?: number }) {
  const { sort, limit = 20, offset = 0 } = params
  return request<PostItem[]>({
    url: `${PREFIX}${queryString({ sort, limit, offset })}`,
    method: 'GET',
  })
}

/** 帖子详情 */
export function getPostDetail(postId: string) {
  return request<PostItem>({ url: `${PREFIX}/${postId}`, method: 'GET' })
}

/** 发帖（发布后 risk_status=pending，异步风控） */
export function createPost(data: PostCreateParams, options?: Partial<RequestOptions>) {
  return request<PostItem>({ url: PREFIX, method: 'POST', data, ...options })
}

// ==================== 关注流 ====================

export interface FeedListRes {
  items: PostItem[]
  total: number
}

/** 获取关注流（我关注的人发布的帖子） */
export function getFeed(params?: { limit?: number; offset?: number }): Promise<FeedListRes> {
  const { limit = 20, offset = 0 } = params || {}
  return request<FeedListRes>({
    url: `/api/v1/user/me/feed?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

// ==================== 搜索 ====================

export interface SearchParams {
  keyword?: string
  tags?: string[]
  user_id?: string
  industry?: string
  city?: string
  salary_range?: string
  sort?: 'hot' | 'latest'
  limit?: number
  offset?: number
}

/** 搜索帖子 */
export function searchPosts(params: SearchParams): Promise<FeedListRes> {
  const {
    keyword,
    tags,
    user_id,
    industry,
    city,
    salary_range,
    sort = 'latest',
    limit = 20,
    offset = 0,
  } = params

  const query: Record<string, string | number> = { sort, limit, offset }
  if (keyword) query.keyword = keyword
  if (tags && tags.length > 0) query.tags = tags.join(',')
  if (user_id) query.user_id = user_id
  if (industry) query.industry = industry
  if (city) query.city = city
  if (salary_range) query.salary_range = salary_range

  return request<FeedListRes>({
    url: `${PREFIX}/search${queryString(query)}`,
    method: 'GET',
  })
}
