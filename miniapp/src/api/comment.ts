/**
 * 评论 - 与 backend /api/v1/posts 下评论接口一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/posts'

export interface CommentItem {
  id: string
  post_id: string
  user_id: string
  anonymous_name: string
  content: string
  parent_id: string | null
  like_count: number
  risk_status: string
  created_at: string
  updated_at: string
  replies?: CommentItem[] | null
}

/** 帖子下评论列表（根评论分页，带二级回复） */
export function getCommentList(
  postId: string,
  params?: { limit?: number; offset?: number }
) {
  const { limit = 20, offset = 0 } = params ?? {}
  const q = `limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`
  return request<CommentItem[]>({
    url: `${PREFIX}/${postId}/comments?${q}`,
    method: 'GET',
  })
}

/** 发表评论或回复：不传 parentId 为根评论，传 parentId 为回复 */
export function createComment(
  postId: string,
  data: { content: string; parent_id?: string | null }
) {
  return request<CommentItem>({
    url: `${PREFIX}/${postId}/comments`,
    method: 'POST',
    data: { content: data.content, parent_id: data.parent_id ?? undefined },
  })
}

/** 删除评论（仅本人可删），204 无 body */
export function deleteComment(commentId: string) {
  return request<void>({
    url: `${PREFIX}/comments/${commentId}`,
    method: 'DELETE',
  })
}
