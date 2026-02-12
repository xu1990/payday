/**
 * 话题管理 API
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/admin/topics'

export interface TopicItem {
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

export interface TopicCreate {
  name: string
  description?: string | null
  cover_image?: string | null
  sort_order?: number
}

export interface TopicUpdate {
  name?: string
  description?: string | null
  cover_image?: string | null
  is_active?: boolean
  sort_order?: number
}

export interface TopicListResult {
  items: TopicItem[]
  total: number
}

/** 话题列表 */
export function listTopics(params?: {
  active_only?: boolean
  limit?: number
  offset?: number
}) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<TopicListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建话题 */
export function createTopic(data: TopicCreate) {
  return request<TopicItem>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 获取单个话题 */
export function getTopic(topicId: string) {
  return request<TopicItem>({
    url: `${PREFIX}/${topicId}`,
    method: 'GET',
  })
}

/** 更新话题 */
export function updateTopic(topicId: string, data: TopicUpdate) {
  return request<TopicItem>({
    url: `${PREFIX}/${topicId}`,
    method: 'PUT',
    data,
  })
}

/** 删除话题 */
export function deleteTopic(topicId: string) {
  return request<{ deleted: boolean }>({
    url: `${PREFIX}/${topicId}`,
    method: 'DELETE',
  })
}
