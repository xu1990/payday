<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getFeed, type PostItem } from '@/api/post'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const posts = ref<PostItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(true)

async function loadData(append = false) {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }

  loading.value = true
  try {
    const res = await getFeed({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })

    const newPosts = res?.items || []

    if (append) {
      posts.value = [...posts.value, ...newPosts]
    } else {
      posts.value = newPosts
    }

    hasMore.value = posts.value.length < (res?.total || 0)
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    uni.showToast({ title: errorMessage, icon: 'none' })
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  currentPage.value++
  loadData(true) // 追加模式
}

function refresh() {
  currentPage.value = 1
  loadData()
}

function goToDetail(post: PostItem) {
  uni.navigateTo({
    url: '/pages/post-detail/index?id=' + post.id,
  })
}

function formatTime(time: string): string {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return minutes + '分钟前'
  if (hours < 24) return hours + '小时前'
  if (days < 30) return days + '天前'
  return date.toLocaleDateString()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <view class="feed-page">
    <!-- 顶部导航 -->
    <view class="header">
      <text class="title">关注</text>
    </view>

    <!-- 空状态 -->
    <view v-if="!loading && posts.length === 0" class="empty">
      <text>还没有关注任何人，去广场看看吧~</text>
      <view class="empty-action" @tap="() => uni.switchTab({ url: '/pages/square/index' })">
        <text>去广场</text>
      </view>
    </view>

    <!-- 帖子列表 -->
    <view v-else class="post-list">
      <view v-for="post in posts" :key="post.id" class="post-item" @tap="goToDetail(post)">
        <view class="post-header">
          <text class="username">{{ post.anonymous_name }}</text>
          <text class="time">{{ formatTime(post.created_at) }}</text>
        </view>
        <view class="post-content">
          <text class="content-text">{{ post.content }}</text>
        </view>
        <view class="post-stats">
          <text class="stat">❤️ {{ post.like_count || 0 }}</text>
          <text class="stat">💬 {{ post.comment_count || 0 }}</text>
        </view>
      </view>

      <view v-if="hasMore" class="load-more" @tap="loadMore">
        <text v-if="loading">加载中...</text>
        <text v-else>加载更多</text>
      </view>
      <view v-else-if="posts.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>
    </view>

    <view v-if="loading && posts.length === 0" class="loading-wrapper">
      <text>加载中...</text>
    </view>
  </view>
</template>

<style scoped>
.feed-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
.header {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  background-color: #fff;
}
.title {
  font-size: 17px;
  font-weight: 600;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 60rpx;
}
.empty text {
  color: #999;
  margin-bottom: 30rpx;
}
.empty-action {
  padding: 16rpx 40rpx;
  background-color: #07c160;
  border-radius: 40rpx;
}
.empty-action text {
  color: #fff;
}
.post-list {
  padding-bottom: 20rpx;
}
.post-item {
  background-color: #fff;
  margin-bottom: 20rpx;
  padding: 30rpx;
}
.post-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20rpx;
}
.username {
  font-size: 16px;
  font-weight: 600;
}
.time {
  font-size: 12px;
  color: #999;
}
.content-text {
  font-size: 15px;
  line-height: 1.6;
}
.post-stats {
  display: flex;
  gap: 40rpx;
  margin-top: 20rpx;
}
.stat {
  font-size: 13px;
  color: #999;
}
.load-more {
  padding: 30rpx;
  text-align: center;
  color: #666;
}
.no-more {
  padding: 30rpx;
  text-align: center;
  color: #999;
}
.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx;
  color: #999;
}
</style>
