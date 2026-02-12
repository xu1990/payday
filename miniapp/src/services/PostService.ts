/**
 * 帖子服务 - 处理帖子相关业务逻辑
 */
import { BaseService } from './base/BaseService'
import type { PostItem, PostCreateParams } from '@/api/post'

export class PostService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/posts'
  }

  /**
   * 获取帖子列表
   */
  async getPosts(params: {
    limit?: number
    offset?: number
    sort?: 'hot' | 'latest'
  }) {
    return this.get<PostItem[]>('', params)
  }

  /**
   * 获取帖子详情
   */
  async getPostDetail(postId: string) {
    return this.get<PostItem>(`/${postId}`)
  }

  /**
   * 创建帖子
   */
  async createPost(data: PostCreateParams) {
    return this.post<PostItem>('', data)
  }

  /**
   * 删除帖子
   */
  async deletePost(postId: string) {
    return this.delete<boolean>(`/${postId}`)
  }

  /**
   * 获取我的帖子
   */
  async getMyPosts(params: { limit?: number; offset?: number }) {
    return this.get<PostItem[]>('/my', params)
  }
}

// 导出单例
export const postService = new PostService()
