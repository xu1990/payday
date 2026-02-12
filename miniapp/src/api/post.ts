/**
 * 帖子 - 与 backend /api/v1/posts 一致
 */
import request from '@/utils/request'

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
export function createPost(data: PostCreateParams) {
  return request<PostItem>({ url: PREFIX, method: 'POST', data })
}
