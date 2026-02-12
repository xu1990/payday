/**
 * 点赞 - 与 backend /api/v1 下 like 路由一致（无 prefix，路径为 /posts/:id/like、/comments/:id/like）
 */
import request from '@/utils/request'

const PREFIX = '/api/v1'

/** 帖子点赞；已赞幂等返回 200，新赞 201 */
export function likePost(postId: string) {
  return request<{ id: string; user_id: string; target_type: string; target_id: string; created_at: string }>({
    url: `${PREFIX}/posts/${postId}/like`,
    method: 'POST',
  })
}

/** 取消帖子点赞 */
export function unlikePost(postId: string) {
  return request<void>({
    url: `${PREFIX}/posts/${postId}/like`,
    method: 'DELETE',
  })
}

/** 评论点赞；已赞幂等返回 200，新赞 201 */
export function likeComment(commentId: string) {
  return request<{ id: string; user_id: string; target_type: string; target_id: string; created_at: string }>({
    url: `${PREFIX}/comments/${commentId}/like`,
    method: 'POST',
  })
}

/** 取消评论点赞 */
export function unlikeComment(commentId: string) {
  return request<void>({
    url: `${PREFIX}/comments/${commentId}/like`,
    method: 'DELETE',
  })
}
