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
  const queryParts: string[] = []
  if (params) {
    if (params.keyword) queryParts.push(`keyword=${encodeURIComponent(params.keyword)}`)
    if (params.tags) queryParts.push(`tags=${encodeURIComponent(params.tags)}`)
    if (params.user_id) queryParts.push(`user_id=${encodeURIComponent(params.user_id)}`)
    if (params.industry) queryParts.push(`industry=${encodeURIComponent(params.industry)}`)
    if (params.city) queryParts.push(`city=${encodeURIComponent(params.city)}`)
    if (params.salary_range)
      queryParts.push(`salary_range=${encodeURIComponent(params.salary_range)}`)
    if (params.sort) queryParts.push(`sort=${encodeURIComponent(params.sort)}`)
    if (params.limit != null) queryParts.push(`limit=${encodeURIComponent(String(params.limit))}`)
    if (params.offset != null)
      queryParts.push(`offset=${encodeURIComponent(String(params.offset))}`)
  }
  const qs = queryParts.join('&')
  const url = qs ? `${PREFIX}/search?${qs}` : PREFIX
  return request<SearchRes>({ url, method: 'GET' })
}
