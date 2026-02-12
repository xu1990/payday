/**
 * 推荐内容 API
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/recommendations'

/** 热门帖子推荐 */
export function getHotPosts(limit?: number) {
  return request({
    url: PREFIX + '/hot',
    method: 'GET',
    params: { limit: limit || 10 },
  })
}

/** 个性化推荐（需要登录） */
export function getPersonalizedFeed(limit?: number) {
  return request({
    url: PREFIX + '/feed',
    method: 'GET',
    params: { limit: limit || 20 },
  })
}

/** 推荐话题 */
export function getRecommendedTopics(limit?: number) {
  return request<{ items: TopicItem[] }>({
    url: PREFIX + '/topics',
    method: 'GET',
    params: { limit: limit || 10 },
  })
}

/** 推荐话题项 */
export interface TopicItem {
  id: string
  name: string
  description: string | null
  cover_image: string | null
  post_count: number
}
