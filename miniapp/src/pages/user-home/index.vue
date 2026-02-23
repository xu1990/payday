<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getPostList, type PostItem } from '@/api/post'
import { getCheckinList, type CheckinItem } from '@/api/checkin'
import { getUserProfile, getFollowStatus } from '@/api/user'
import { useAuthStore } from '@/stores/auth'
import FollowButton from '@/components/FollowButton.vue'
import { formatDate as format } from '@/utils/format'

const targetUserId = ref('')
const authStore = useAuthStore()
const loading = ref(true)
const error = ref<string | null>(null)
const posts = ref<PostItem[]>([])
const checkins = ref<CheckinItem[]>([])
const followerCount = ref(0)
const followingCount = ref(0)
const currentTab = ref<'posts' | 'checkins'>('posts')
const postPage = ref({ limit: 20, offset: 0 })
const checkinPage = ref({ limit: 30, offset: 0 })
const hasMore = ref(true)
const loadingMore = ref(false)
const isFollowing = ref(false)

const isOwnProfile = computed(() => {
  return authStore.user?.id === targetUserId.value
})

onLoad((options: any) => {
  targetUserId.value = options?.userId || ''
  if (targetUserId.value) {
    loadProfileData()
  } else {
    loading.value = false
  }
})

async function checkFollowStatus() {
  if (isOwnProfile.value) return

  try {
    const result = await getFollowStatus(targetUserId.value)
    isFollowing.value = result.is_following || false
  } catch (e) {
    // Ignore error, default to not following
    console.error('Failed to check follow status:', e)
  }
}

async function loadProfileData() {
  loading.value = true
  error.value = null
  try {
    // 获取用户主页数据
    const data = await getUserProfile(targetUserId.value)

    followerCount.value = data.user.follower_count
    followingCount.value = data.user.following_count

    // 加载帖子详情
    if (data.posts?.length) {
      const postsResult = await getPostList({ limit: 20, offset: 0, user_id: targetUserId.value })
      posts.value = postsResult.items || []
    }

    // 加载签到详情
    if (data.checkins?.length) {
      const checkinsResult = await getCheckinList({ limit: 30, offset: 0 })
      checkins.value = checkinsResult.items || []
    }

    // Check follow status
    await checkFollowStatus()
  } catch (e) {
    console.error('Failed to load user profile:', e)
    error.value = '加载失败'
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  try {
    if (currentTab.value === 'posts') {
      postPage.value.offset += postPage.value.limit
      const result = await getPostList({
        limit: postPage.value.limit,
        offset: postPage.value.offset,
        user_id: targetUserId.value,
      })
      posts.value.push(...(result.items || []))
      hasMore.value = (result.items || []).length >= postPage.value.limit
    } else {
      checkinPage.value.offset += checkinPage.value.limit
      const result = await getCheckinList({
        limit: checkinPage.value.limit,
        offset: checkinPage.value.offset,
      })
      checkins.value.push(...(result.items || []))
      hasMore.value = (result.items || []).length >= checkinPage.value.limit
    }
  } catch (e) {
    // Failed to load more
  } finally {
    loadingMore.value = false
  }
}

async function handleFollow() {
  if (!authStore.isLoggedIn) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }
  // Only update local state - FollowButton already made the API call
  isFollowing.value = true
  followerCount.value += 1
}

async function handleUnfollow() {
  if (!authStore.isLoggedIn) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }
  // Only update local state - FollowButton already made the API call
  isFollowing.value = false
  followerCount.value = Math.max(0, followerCount.value - 1)
}

function switchTab(tab: 'posts' | 'checkins') {
  currentTab.value = tab
  hasMore.value = true
}

function formatDate(dateStr: string) {
  return format(dateStr)
}

function goToFollowerList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=followers&userId=${targetUserId.value}`,
  })
}

function goToFollowingList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=following&userId=${targetUserId.value}`,
  })
}

function goToPost(postId: string) {
  uni.navigateTo({
    url: `/pages/post-detail/index?id=${postId}`,
  })
}
</script>

<template>
  <view class="page">
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else class="content">
      <!-- 用户统计 -->
      <view class="stats-card">
        <FollowButton
          v-if="!isOwnProfile && authStore.isLoggedIn"
          :target-user-id="targetUserId"
          :is-following="isFollowing"
          @follow="handleFollow"
          @unfollow="handleUnfollow"
        />
        <view class="stat-item" @tap="goToFollowerList">
          <text class="stat-value">{{ followerCount }}</text>
          <text class="stat-label">粉丝</text>
        </view>
        <view class="stat-item" @tap="goToFollowingList">
          <text class="stat-value">{{ followingCount }}</text>
          <text class="stat-label">关注</text>
        </view>
      </view>

      <!-- 标签切换 -->
      <view class="tabs">
        <view class="tab" :class="{ active: currentTab === 'posts' }" @tap="switchTab('posts')">
          帖子 {{ posts.length > 0 ? `(${posts.length})` : '' }}
        </view>
        <view
          class="tab"
          :class="{ active: currentTab === 'checkins' }"
          @tap="switchTab('checkins')"
        >
          签到 {{ checkins.length > 0 ? `(${checkins.length})` : '' }}
        </view>
      </view>

      <!-- 帖子列表 -->
      <view v-if="currentTab === 'posts'" class="list">
        <view v-if="!posts.length" class="tip">暂无帖子</view>
        <view v-for="post in posts" :key="post.id" class="post-card" @tap="goToPost(post.id)">
          <view class="post-header">
            <text class="post-name">{{ post.anonymous_name }}</text>
            <text class="post-time">{{ formatDate(post.created_at) }}</text>
          </view>
          <text class="post-content">{{ post.content }}</text>
          <view class="post-meta">
            <text>👍 {{ post.like_count }}</text>
            <text>💬 {{ post.comment_count }}</text>
            <text>👁 {{ post.view_count }}</text>
          </view>
        </view>
      </view>

      <!-- 签到列表 -->
      <view v-if="currentTab === 'checkins'" class="list">
        <view v-if="!checkins.length" class="tip">暂无签到记录</view>
        <view v-for="checkin in checkins" :key="checkin.id" class="checkin-card">
          <view class="checkin-header">
            <text class="checkin-date">{{ formatDate(checkin.check_date) }}</text>
            <text class="checkin-mood">{{ checkin.mood_emoji }} {{ checkin.mood_text }}</text>
          </view>
          <text v-if="checkin.note" class="checkin-note">{{ checkin.note }}</text>
          <view v-if="checkin.salary_info" class="checkin-salary">
            <text class="salary-label">工资到账：</text>
            <text class="salary-value">{{ checkin.salary_info }}</text>
          </view>
        </view>
      </view>

      <!-- 加载更多 -->
      <view v-if="hasMore && (posts.length || checkins.length)" class="load-more" @tap="loadMore">
        <text>{{ loadingMore ? '加载中...' : '加载更多' }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
}
.tip {
  padding: 48rpx;
  text-align: center;
  color: #999;
}
.content {
  padding: 24rpx;
}
.stats-card {
  display: flex;
  justify-content: space-around;
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx 0;
  margin-bottom: 24rpx;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  cursor: pointer;
  transition: transform 0.1s;
}

.stat-item:active {
  transform: scale(0.95);
}
.stat-value {
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
}
.stat-label {
  font-size: 24rpx;
  color: #999;
}
.tabs {
  display: flex;
  background: #fff;
  border-radius: 16rpx;
  padding: 8rpx;
  margin-bottom: 24rpx;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 16rpx;
  font-size: 28rpx;
  color: #666;
  border-radius: 12rpx;
}
.tab.active {
  background: #07c160;
  color: #fff;
  font-weight: 500;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.post-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.post-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}
.post-time {
  font-size: 22rpx;
  color: #999;
}
.post-content {
  font-size: 28rpx;
  line-height: 1.6;
  color: #666;
  display: block;
  margin-bottom: 16rpx;
}
.post-meta {
  display: flex;
  gap: 24rpx;
  font-size: 24rpx;
  color: #999;
}
.checkin-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}
.checkin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.checkin-date {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}
.checkin-mood {
  font-size: 26rpx;
  color: #666;
}
.checkin-note {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 12rpx;
  line-height: 1.5;
}
.checkin-salary {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.salary-label {
  font-size: 24rpx;
  color: #999;
}
.salary-value {
  font-size: 28rpx;
  color: #07c160;
  font-weight: 500;
}
.load-more {
  padding: 32rpx;
  text-align: center;
  color: #07c160;
  font-size: 28rpx;
}
</style>
