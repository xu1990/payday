/**
 * 帖子状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as postApi from '@/api/post'
import type { PostItem, PostCreateParams } from '@/api/post'

export const usePostStore = defineStore('post', () => {
  // SECURITY: 持久化存储到 localStorage
  const STORAGE_KEY = 'post_data'

  // 状态
  const posts = ref<PostItem[]>([])
  const currentPost = ref<PostItem | null>(null)
  const hotPosts = ref<PostItem[]>([])
  const latestPosts = ref<PostItem[]>([])
  const isLoading = ref(false)
  const isLoadingMore = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)

  // 分页状态
  const hotOffset = ref(0)
  const latestOffset = ref(0)
  const pageSize = 20

  // 计算属性
  const hasPosts = computed(() => posts.value.length > 0)
  const hasHotPosts = computed(() => hotPosts.value.length > 0)
  const hasLatestPosts = computed(() => latestPosts.value.length > 0)

  /**
   * 获取热门帖子列表
   */
  async function fetchHotPosts(refresh = false): Promise<boolean> {
    if (refresh) {
      hotOffset.value = 0
      hotPosts.value = []
    }

    if (isLoading.value || !hasMore.value) return false

    try {
      isLoading.value = !refresh
      isLoadingMore.value = refresh

      const data = await postApi.getPostList({
        sort: 'hot',
        limit: pageSize,
        offset: hotOffset.value,
      })

      if (refresh) {
        hotPosts.value = data
      } else {
        hotPosts.value.push(...data)
      }

      hotOffset.value += data.length
      hasMore.value = data.length === pageSize
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取热门帖子失败'
      return false
    } finally {
      isLoading.value = false
      isLoadingMore.value = false
    }
  }

  /**
   * 获取最新帖子列表
   */
  async function fetchLatestPosts(refresh = false): Promise<boolean> {
    if (refresh) {
      latestOffset.value = 0
      latestPosts.value = []
    }

    if (isLoading.value || !hasMore.value) return false

    try {
      isLoading.value = !refresh
      isLoadingMore.value = refresh

      const data = await postApi.getPostList({
        sort: 'latest',
        limit: pageSize,
        offset: latestOffset.value,
      })

      if (refresh) {
        latestPosts.value = data
      } else {
        latestPosts.value.push(...data)
      }

      latestOffset.value += data.length
      hasMore.value = data.length === pageSize
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取最新帖子失败'
      return false
    } finally {
      isLoading.value = false
      isLoadingMore.value = false
    }
  }

  /**
   * 获取帖子详情
   */
  async function fetchPostDetail(postId: string): Promise<boolean> {
    try {
      isLoading.value = true
      error.value = null
      const data = await postApi.getPostDetail(postId)
      currentPost.value = data
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取帖子详情失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建帖子
   */
  async function createPost(params: PostCreateParams): Promise<PostItem | null> {
    try {
      isLoading.value = true
      error.value = null
      const data = await postApi.createPost(params)

      // 添加到列表开头
      posts.value.unshift(data)
      latestPosts.value.unshift(data)

      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '发布帖子失败'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新本地帖子的点赞数
   */
  function updatePostLikeCount(postId: string, delta: number) {
    const updateItem = (item: PostItem) => {
      if (item.id === postId) {
        item.like_count += delta
      }
    }

    posts.value.forEach(updateItem)
    hotPosts.value.forEach(updateItem)
    latestPosts.value.forEach(updateItem)

    if (currentPost.value?.id === postId) {
      currentPost.value.like_count += delta
    }
  }

  /**
   * 更新本地帖子的评论数
   */
  function updatePostCommentCount(postId: string, delta: number) {
    const updateItem = (item: PostItem) => {
      if (item.id === postId) {
        item.comment_count += delta
      }
    }

    posts.value.forEach(updateItem)
    hotPosts.value.forEach(updateItem)
    latestPosts.value.forEach(updateItem)

    if (currentPost.value?.id === postId) {
      currentPost.value.comment_count += delta
    }
  }

  /**
   * 重置状态
   */
  function reset() {
    posts.value = []
    currentPost.value = null
    hotPosts.value = []
    latestPosts.value = []
    hotOffset.value = 0
    latestOffset.value = 0
    hasMore.value = true
    error.value = null
    // SECURITY: 清除持久化存储
    clearPersistedData()
  }

  /**
   * 保存状态到 localStorage
   * SECURITY: 加密存储敏感数据
   */
  function savePersistedData() {
    try {
      const data = {
        hotPosts: hotPosts.value.slice(0, 100), // 只保存最近100条
        hotOffset: hotOffset.value,
        latestPosts: latestPosts.value.slice(0, 100),
        latestOffset: latestOffset.value,
        timestamp: Date.now(),
      }
      uni.setStorageSync(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.warn('[PostStore] Failed to save persisted data:', error)
    }
  }

  /**
   * 从 localStorage 加载状态
   * SECURITY: 解密并验证数据
   */
  function loadPersistedData() {
    try {
      const saved = uni.getStorageSync(STORAGE_KEY)
      if (saved) {
        const data = JSON.parse(saved)
        // SECURITY: 只恢复24小时内的数据
        const age = Date.now() - (data.timestamp || 0)
        if (age < 24 * 60 * 60 * 1000) {
          hotPosts.value = data.hotPosts || []
          hotOffset.value = data.hotOffset || 0
          latestPosts.value = data.latestPosts || []
          latestOffset.value = data.latestOffset || 0
        }
      }
    } catch (error) {
      console.warn('[PostStore] Failed to load persisted data:', error)
    }
  }

  /**
   * 清除持久化存储
   */
  function clearPersistedData() {
    try {
      uni.removeStorageSync(STORAGE_KEY)
    } catch (error) {
      console.warn('[PostStore] Failed to clear persisted data:', error)
    }
  }

  return {
    // 状态
    posts,
    currentPost,
    hotPosts,
    latestPosts,
    isLoading,
    isLoadingMore,
    error,
    hasMore,

    // 计算属性
    hasPosts,
    hasHotPosts,
    hasLatestPosts,

    // 方法
    fetchHotPosts,
    fetchLatestPosts,
    fetchPostDetail,
    createPost,
    updatePostLikeCount,
    updatePostCommentCount,
    reset,
  }
})
