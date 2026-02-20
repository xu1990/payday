<script setup lang="ts">
import { ref, watch } from 'vue'
import { getPostList, type PostItem } from '@/api/post'
import { useDebounceFn } from '@/composables/useDebounce'
import { useAuthStore } from '@/stores/auth'
import PostActionBar from '@/components/PostActionBar.vue'

type Sort = 'hot' | 'latest'
const activeTab = ref<Sort>('hot')
const list = ref<PostItem[]>([])
const likedSet = ref<Set<string>>(new Set())
const loading = ref(false)
const authStore = useAuthStore()

function formatTime(created_at: string) {
  const d = new Date(created_at)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  return d.toLocaleDateString()
}

async function load() {
  loading.value = true
  try {
    const result = await getPostList({ sort: activeTab.value, limit: 20, offset: 0 })
    console.log('[Square] API returned:', result)
    console.log('[Square] Array length:', Array.isArray(result) ? result.length : 'Not an array')
    list.value = result
  } catch (error) {
    console.error('[Square] Load failed:', error)
    list.value = []
  } finally {
    loading.value = false
  }
}

// 使用防抖来避免快速切换 tab 导致多次请求
const { run: debouncedLoad } = useDebounceFn(load, 300)

watch(activeTab, debouncedLoad, { immediate: true })

async function handleLike(data: { postId: string; isLiked: boolean }) {
  const { postId, isLiked } = data
  const post = list.value.find(p => p.id === postId)
  if (!post) return

  // Optimistic update
  if (isLiked) {
    likedSet.value.add(postId)
    post.like_count += 1
  } else {
    likedSet.value.delete(postId)
    post.like_count = Math.max(0, post.like_count - 1)
  }
}

function handleComment(data: { postId: string }) {
  goDetail(data.postId)
}

function handleShare(data: { postId: string }) {
  goDetail(data.postId)
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/post-detail/index?id=${id}` })
}

function goCreate() {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }
  uni.navigateTo({ url: '/pages/post-create/index' })
}
</script>

<template>
  <view class="page">
    <view class="tabs">
      <view
        class="tab"
        :class="{ active: activeTab === 'hot' }"
        @click="activeTab = 'hot'"
      >
        热门
      </view>
      <view
        class="tab"
        :class="{ active: activeTab === 'latest' }"
        @click="activeTab = 'latest'"
      >
        最新
      </view>
    </view>
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="list.length === 0" class="tip">暂无帖子</view>
    <scroll-view v-else class="list" scroll-y>
      <view
        v-for="item in list"
        :key="item.id"
        class="card"
        @click="goDetail(item.id)"
      >
        <view class="row">
          <text class="name">{{ item.anonymous_name }}</text>
          <text class="time">{{ formatTime(item.created_at) }}</text>
        </view>
        <text class="content">{{ item.content }}</text>
        <view v-if="item.images?.length" class="imgs">
          <image
            v-for="(img, i) in (item.images || []).slice(0, 3)"
            :key="i"
            class="thumb"
            :src="img"
            mode="aspectFill"
          />
        </view>
        <PostActionBar
          :post-id="item.id"
          :like-count="item.like_count"
          :comment-count="item.comment_count"
          :is-liked="likedSet.has(item.id)"
          :compact="true"
          :show-view="false"
          @like="handleLike"
          @comment="handleComment"
          @share="handleShare"
        />
      </view>
    </scroll-view>
    <view class="fab" @click="goCreate">发帖</view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 120rpx;
  background: #f5f5f5;
}
.tabs {
  display: flex;
  background: #fff;
  padding: 0 24rpx;
  border-bottom: 1rpx solid #eee;
}
.tab {
  padding: 24rpx 32rpx;
  font-size: 30rpx;
  color: #666;
}
.tab.active {
  color: #07c160;
  font-weight: 600;
  border-bottom: 4rpx solid #07c160;
}
.tip {
  padding: 48rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}
.list {
  height: calc(100vh - 100rpx);
}
.card {
  margin: 24rpx;
  padding: 24rpx;
  background: #fff;
  border-radius: 16rpx;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.name {
  font-weight: 600;
  font-size: 28rpx;
}
.time {
  font-size: 24rpx;
  color: #999;
}
.content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  display: block;
}
.imgs {
  display: flex;
  gap: 12rpx;
  margin-top: 16rpx;
}
.thumb {
  width: 160rpx;
  height: 160rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
}
.fab {
  position: fixed;
  right: 32rpx;
  bottom: 120rpx;
  width: 100rpx;
  height: 100rpx;
  line-height: 100rpx;
  text-align: center;
  background: #07c160;
  color: #fff;
  border-radius: 50%;
  font-size: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(7, 193, 96, 0.4);
}
</style>
