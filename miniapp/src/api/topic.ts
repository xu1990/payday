/**
 * 话题相关 API
 */
import request from '@/utils/request'

export interface Topic {
  id: string
  name: string
  description: string | null
  cover_image: string | null
  post_count: number
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string | null
}

/**
 * 获取启用的话题列表（公开接口）
 */
export async function getActiveTopics(): Promise<Topic[]> {
  const res: any = await request({
    url: '/api/v1/topics/active',
    method: 'GET',
  })
  return res.data || []
}
