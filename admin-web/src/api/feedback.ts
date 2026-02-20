/**
 * 反馈相关 API
 */
import adminApi from './admin'

export interface FeedbackItem {
  id: string
  user_id: string
  content: string
  images: string[]
  contact: string | null
  status: 'pending' | 'processing' | 'resolved'
  admin_reply: string | null
  created_at: string
}

/**
 * 获取反馈列表（管理员）
 */
export function getFeedbackList(): Promise<{ data: FeedbackItem[]; message: string }> {
  return adminApi.get('/feedback/')
}

export default {
  getFeedbackList
}
