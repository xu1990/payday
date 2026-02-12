/**
 * 帖子搜索 - 与 backend /api/v1/posts/search 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/posts'

/** 帖子项（搜索结果） */
export interface PostItem {
  id: string
  user_id: string
  anonymous_name: string
  content: string
  images?: string[] | null
  type: string
  salary_range?: string | null
  industry?: string | null
  city?: string | null
  tags?: string[] | null
  view_count: number
  like_count: number
  comment_count: number
  status: string
  risk_status: string
  created_at: string
  updated_at: string
}

/** 搜索请求参数 */
export interface SearchParams {
  keyword?: string
  tags?: string
  user_id?: string
  industry?: string
  city?: string
  salary_range?: string
  sort?: 'hot' | 'latest'
  limit?: number
  offset?: number
}

/** 搜索响应 */
export interface SearchRes {
  items: PostItem[]
  total: number
}

/** 搜索帖子 */
export function searchPosts(params?: SearchParams) {
  const query = new URLSearchParams()
  if (params) {
    if (params.keyword) query.set('keyword', params.keyword)
    if (params.tags) query.set('tags', params.tags)
    if (params.user_id) query.set('user_id', params.user_id)
    if (params.industry) query.set('industry', params.industry)
    if (params.city) query.set('city', params.city)
    if (params.salary_range) query.set('salary_range', params.salary_range)
    if (params.sort) query.set('sort', params.sort)
    if (params.limit != null) query.set('limit', String(params.limit))
    if (params.offset != null) query.set('offset', String(params.offset))
  }
  const qs = query.toString()
  const url = qs ? `${PREFIX}/search?${qs}` : PREFIX
  return request<SearchRes>({ url, method: 'GET' })
}
