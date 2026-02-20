/**
 * 反馈相关 API
 */
import { request } from '@/utils/request'

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
  return request({
    url: '/api/v1/feedback',
    method: 'GET'
  })
}

export default {
  getFeedbackList
}
