<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { getPostList, getMyPosts, type PostItem } from '@/api/post'
import { checkBatchFollowStatus } from '@/api/follow'
import { useDebounceFn } from '@/composables/useDebounce'
import { useAuthStore } from '@/stores/auth'
import GlassTabBar from '@/components/GlassTabBar.vue'
import PostActionBar from '@/components/PostActionBar.vue'
import FollowButton from '@/components/FollowButton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatRelativeTime } from '@/utils/format'

type TabType = 'hot' | 'latest' | 'mine'
const activeTab = ref<TabType>('hot')
const list = ref<PostItem[]>([])
const myPosts = ref<PostItem[]>([])
const myPostsTotal = ref(0)
const followingSet = ref<Set<string>>(new Set())
const loading = ref(false)
const authStore = useAuthStore()

// 状态标签映射
const statusLabelMap: Record<string, { text: string; class: string }> = {
  approved: { text: '已通过', class: 'status-approved' },
  pending: { text: '待审核', class: 'status-pending' },
  rejected: { text: '已拒绝', class: 'status-rejected' },
}

const riskStatusLabel = computed(() => {
  return (post: PostItem) => {
    const label = statusLabelMap[post.risk_status]
    return label || { text: post.risk_status, class: '' }
  }
})

function formatTime(created_at: string) {
  return formatRelativeTime(created_at)
}

async function load() {
  loading.value = true
  followingSet.value.clear()

  try {
    if (activeTab.value === 'mine') {
      // 加载我的帖子
      await loadMyPosts()
    } else {
      // 加载广场帖子
      const result = await getPostList({ sort: activeTab.value, limit: 20, offset: 0 })
      list.value = result
      await fetchFollowStatus()
    }
  } catch (error) {
    console.error('[Square] Load failed:', error)
    list.value = []
    myPosts.value = []
  } finally {
    loading.value = false
  }
}

async function loadMyPosts() {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }

  const result = await getMyPosts({ limit: 50, offset: 0 })
  myPosts.value = result.items || []
  myPostsTotal.value = result.total || 0
}

async function fetchFollowStatus() {
  if (!authStore.isLoggedIn) return

  // Get unique author IDs from posts
  const authorIds = [...new Set(list.value.map(p => p.user_id))]
  if (authorIds.length === 0) return

  try {
    const statusMap = await checkBatchFollowStatus(authorIds)
    followingSet.value = new Set(
      Object.entries(statusMap)
        .filter(([, isFollowing]) => isFollowing)
        .map(([userId]) => userId)
    )
  } catch (e) {
    console.error('[Square] Failed to fetch follow status:', e)
  }
}

// 使用防抖来避免快速切换 tab 导致多次请求
const { run: debouncedLoad } = useDebounceFn(load, 300)

watch(activeTab, debouncedLoad, { immediate: true })

async function handleLike(data: { postId: string; isLiked: boolean }) {
  const { postId, isLiked } = data
  const post = list.value.find(p => p.id === postId)
  if (!post) return

  // Optimistic update - use API's is_liked field
  post.is_liked = isLiked
  if (isLiked) {
    post.like_count += 1
  } else {
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

function handleFollow(data: { targetUserId: string }) {
  followingSet.value.add(data.targetUserId)
}

function handleUnfollow(data: { targetUserId: string }) {
  followingSet.value.delete(data.targetUserId)
}

function handleMyPostClick(item: PostItem) {
  // 如果帖子被拒绝（下架），跳转到编辑页面
  if (item.risk_status === 'rejected' || item.status === 'hidden') {
    uni.navigateTo({ url: `/pages/post-create/index?id=${item.id}&edit=1` })
  } else {
    goDetail(item.id)
  }
}

function editPost(item: PostItem) {
  uni.navigateTo({ url: `/pages/post-create/index?id=${item.id}&edit=1` })
}
</script>

<template>
  <view class="page">
    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'hot' }" @click="activeTab = 'hot'">
        热门
      </view>
      <view class="tab" :class="{ active: activeTab === 'latest' }" @click="activeTab = 'latest'">
        最新
      </view>
      <view class="tab" :class="{ active: activeTab === 'mine' }" @click="activeTab = 'mine'">
        我的
      </view>
    </view>
    <view v-if="loading" class="tip">加载中...</view>

    <!-- 广场帖子列表（热门/最新） -->
    <template v-else-if="activeTab !== 'mine'">
      <view v-if="list.length === 0" class="tip">暂无帖子</view>
      <scroll-view v-else class="list" scroll-y>
        <view v-for="item in list" :key="item.id" class="card" @click="goDetail(item.id)">
          <view class="row">
            <view class="author-section">
              <UserAvatar
                :avatar="item.user_avatar"
                :anonymous-name="item.anonymous_name"
                size="small"
              />
              <text class="name">{{ item.anonymous_name }}</text>
              <FollowButton
                v-if="authStore.isLoggedIn && item.user_id !== authStore.user?.id"
                :target-user-id="item.user_id"
                :is-following="followingSet.has(item.user_id)"
                size="small"
                @follow="handleFollow"
                @unfollow="handleUnfollow"
                @click.stop
              />
            </view>
            <text class="time">{{ formatTime(item.created_at) }}</text>
          </view>
          <text class="post-content">{{ item.content }}</text>
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
            :is-liked="item.is_liked ?? false"
            :compact="true"
            :show-view="false"
            @like="handleLike"
            @comment="handleComment"
            @share="handleShare"
          />
        </view>
      </scroll-view>
    </template>

    <!-- 我的帖子列表 -->
    <template v-else>
      <view v-if="!authStore.isLoggedIn" class="tip">
        <text>请先登录查看您的帖子</text>
        <button class="login-btn" @click="uni.navigateTo({ url: '/pages/login/index' })">去登录</button>
      </view>
      <view v-else-if="myPosts.length === 0" class="tip">
        <text>您还没有发布过帖子</text>
        <button class="create-btn" @click="goCreate">去发帖</button>
      </view>
      <scroll-view v-else class="list" scroll-y>
        <view class="my-posts-count">共 {{ myPostsTotal }} 条帖子</view>
        <view v-for="item in myPosts" :key="item.id" class="card my-post-card" @click="handleMyPostClick(item)">
          <view class="row">
            <view class="status-section">
              <text class="status-tag" :class="riskStatusLabel(item).class">
                {{ riskStatusLabel(item).text }}
              </text>
              <text v-if="item.status === 'hidden'" class="status-tag status-hidden">已下架</text>
            </view>
            <text class="time">{{ formatTime(item.created_at) }}</text>
          </view>
          <text class="post-content">{{ item.content }}</text>
          <view v-if="item.images?.length" class="imgs">
            <image
              v-for="(img, i) in (item.images || []).slice(0, 3)"
              :key="i"
              class="thumb"
              :src="img"
              mode="aspectFill"
            />
          </view>
          <view class="my-post-footer">
            <view class="stats">
              <text>赞 {{ item.like_count }}</text>
              <text>评论 {{ item.comment_count }}</text>
              <text>浏览 {{ item.view_count }}</text>
            </view>
            <view
              v-if="item.risk_status === 'rejected' || item.status === 'hidden'"
              class="edit-btn"
              @click.stop="editPost(item)"
            >
              编辑
            </view>
          </view>
        </view>
      </scroll-view>
    </template>

    <view class="fab" @click="goCreate">发帖</view>

    <!-- 液态玻璃 TabBar -->
    <GlassTabBar />
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: env(safe-area-inset-top) 0 120rpx;
  background: var(--bg-base);
}
.tabs {
  display: flex;
  background: var(--bg-glass-subtle);
  padding: 0 $spacing-lg;
  border-bottom: 1rpx solid var(--border-subtle);
}
.tab {
  padding: $spacing-lg $spacing-md;
  font-size: $font-size-base;
  color: var(--text-secondary);
}
.tab.active {
  color: $brand-primary;
  font-weight: $font-weight-semibold;
  border-bottom: 4rpx solid $brand-primary;
}
.tip {
  padding: $spacing-xl;
  text-align: center;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
.list {
  height: calc(100vh - 100rpx);
}
.card {
  @include glass-card();
  margin: $spacing-lg;
  padding: $spacing-lg;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-base;
}
.author-section {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  flex: 1;
}
.name {
  font-weight: $font-weight-semibold;
  font-size: $font-size-sm;
}
.time {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}
.post-content {
  font-size: $font-size-sm;
  color: var(--text-primary);
  line-height: 1.5;
  display: block;
}
.imgs {
  display: flex;
  gap: $spacing-xs;
  margin-top: $spacing-base;
}
.thumb {
  width: 160rpx;
  height: 160rpx;
  border-radius: $radius-sm;
  background: var(--bg-glass-subtle);
}
.fab {
  position: fixed;
  right: $spacing-md;
  bottom: 120rpx;
  width: 100rpx;
  height: 100rpx;
  line-height: 100rpx;
  text-align: center;
  background: $brand-primary;
  color: #fff;
  border-radius: 50%;
  font-size: $font-size-lg;
  box-shadow: $shadow-brand;
}

// 我的帖子相关样式
.my-posts-count {
  padding: $spacing-sm $spacing-lg;
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

.my-post-card {
  .row {
    margin-bottom: $spacing-sm;
  }
}

.status-section {
  display: flex;
  gap: $spacing-xs;
}

.status-tag {
  font-size: $font-size-xs;
  padding: 4rpx 12rpx;
  border-radius: $radius-sm;

  &.status-approved {
    background: rgba(52, 199, 89, 0.15);
    color: #34c759;
  }

  &.status-pending {
    background: rgba(255, 149, 0, 0.15);
    color: #ff9500;
  }

  &.status-rejected {
    background: rgba(255, 59, 48, 0.15);
    color: #ff3b30;
  }

  &.status-hidden {
    background: rgba(142, 142, 147, 0.15);
    color: #8e8e93;
  }
}

.my-post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $spacing-sm;
  padding-top: $spacing-sm;
  border-top: 1rpx solid var(--border-subtle);

  .stats {
    display: flex;
    gap: $spacing-md;
    font-size: $font-size-xs;
    color: var(--text-tertiary);
  }

  .edit-btn {
    font-size: $font-size-xs;
    padding: 8rpx 20rpx;
    background: $brand-primary;
    color: #fff;
    border-radius: $radius-sm;
  }
}

.tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-md;

  .login-btn,
  .create-btn {
    margin-top: $spacing-sm;
    padding: $spacing-sm $spacing-lg;
    font-size: $font-size-sm;
    background: $brand-primary;
    color: #fff;
    border-radius: $radius-full;
    border: none;
  }
}
</style>
