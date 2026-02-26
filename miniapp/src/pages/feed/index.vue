<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { getMyLikes } from '@/api/like'
import { getMyFollowers, getMyFollowing, checkBatchFollowStatus } from '@/api/follow'
import { useAuthStore } from '@/stores/auth'
import FollowButton from '@/components/FollowButton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatRelativeTime } from '@/utils/format'

const authStore = useAuthStore()

// Tab: 'following' | 'likes' | 'followers'
const currentTab = ref('following')

// 用户列表数据（我的关注 / 关注我的）
const users = ref([])
const userLoading = ref(false)
const userTotal = ref(0)
const currentUserPage = ref(1)
const userPageSize = 20
const hasMoreUsers = ref(true)

// 帖子列表数据（我的点赞）
const posts = ref([])
const postLoading = ref(false)
const postTotal = ref(0)
const currentPostPage = ref(1)
const postPageSize = 20
const hasMorePosts = ref(true)

// 当前用户ID
const currentUserId = computed(() => authStore.user?.id || '')

// 加载用户数据
async function loadUsers(append = false) {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }

  userLoading.value = true
  try {
    let res

    if (currentTab.value === 'following') {
      // 我的关注列表
      res = await getMyFollowing({
        limit: userPageSize,
        offset: (currentUserPage.value - 1) * userPageSize,
      })

      // 我的关注列表中的所有用户都已关注
      const newUsers = (res?.items || []).map(u => ({ ...u, is_following: true }))

      if (append) {
        users.value = [...users.value, ...newUsers]
      } else {
        users.value = newUsers
      }
    } else if (currentTab.value === 'followers') {
      // 我的粉丝列表
      res = await getMyFollowers({
        limit: userPageSize,
        offset: (currentUserPage.value - 1) * userPageSize,
      })

      const newUsers = res?.items || []

      // 对于粉丝列表，需要查询关注状态
      if (newUsers.length > 0 && authStore.isLoggedIn) {
        const userIds = newUsers.map(u => u.id)
        try {
          const statusMap = await checkBatchFollowStatus(userIds)
          newUsers.forEach(u => {
            u.is_following = statusMap[u.id] || false
          })
        } catch (e) {
          console.error('[Feed] Failed to fetch follow status:', e)
          // 失败时默认未关注
          newUsers.forEach(u => (u.is_following = false))
        }
      }

      if (append) {
        users.value = [...users.value, ...newUsers]
      } else {
        users.value = newUsers
      }
    }

    hasMoreUsers.value = users.value.length < (res?.total || 0)
    userTotal.value = res?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    uni.showToast({ title: errorMessage, icon: 'none' })
  } finally {
    userLoading.value = false
  }
}

// 加载帖子数据
async function loadPosts(append = false) {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }

  postLoading.value = true
  try {
    const res = await getMyLikes({
      target_type: 'post',
      limit: postPageSize,
      offset: (currentPostPage.value - 1) * postPageSize,
    })

    const newPosts = res?.items || []

    if (append) {
      posts.value = [...posts.value, ...newPosts]
    } else {
      posts.value = newPosts
    }

    hasMorePosts.value = posts.value.length < (res?.total || 0)
    postTotal.value = res?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    uni.showToast({ title: errorMessage, icon: 'none' })
  } finally {
    postLoading.value = false
  }
}

// 加载数据（根据当前tab）
async function loadData(append = false) {
  if (currentTab.value === 'likes') {
    await loadPosts(append)
  } else {
    await loadUsers(append)
  }
}

// 加载更多
function loadMore() {
  if (currentTab.value === 'likes') {
    if (!hasMorePosts.value || postLoading.value) return
    currentPostPage.value++
    loadPosts(true)
  } else {
    if (!hasMoreUsers.value || userLoading.value) return
    currentUserPage.value++
    loadUsers(true)
  }
}

// 刷新
function refresh() {
  if (currentTab.value === 'likes') {
    currentPostPage.value = 1
    loadPosts()
  } else {
    currentUserPage.value = 1
    loadUsers()
  }
}

// 切换tab
function switchTab(tab: 'following' | 'likes' | 'followers') {
  if (currentTab.value === tab) return
  currentTab.value = tab

  // 重置分页
  currentPostPage.value = 1
  currentUserPage.value = 1
  posts.value = []
  users.value = []

  loadData()
}

// 监听tab变化
watch(currentTab, () => {
  loadData()
})

// 处理关注
function handleFollow(data: { targetUserId: string }) {
  const user = users.value.find(u => u.id === data.targetUserId)
  if (user) {
    user.is_following = true
    user.follower_count = (user.follower_count || 0) + 1
  }
}

// 处理取消关注
function handleUnfollow(data: { targetUserId: string }) {
  const user = users.value.find(u => u.id === data.targetUserId)
  if (user) {
    user.is_following = false
    user.follower_count = Math.max((user.follower_count || 1) - 1, 0)
  }
}

// 跳转到帖子详情
function goDetail(id: string) {
  uni.navigateTo({
    url: '/pages/post-detail/index?id=' + id,
  })
}

// 跳转到用户主页
function goToProfile(userId: string) {
  uni.navigateTo({
    url: '/pages/profile/index?id=' + userId,
  })
}

// 格式化时间
function formatTime(created_at: string): string {
  return formatRelativeTime(created_at)
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <view class="page">
    <!-- 顶部导航 -->
    <view class="header">
      <view class="tabs">
        <view
          class="tab"
          :class="{ active: currentTab === 'following' }"
          @tap="() => switchTab('following')"
        >
          <text>我的关注</text>
        </view>
        <view
          class="tab"
          :class="{ active: currentTab === 'likes' }"
          @tap="() => switchTab('likes')"
        >
          <text>我的点赞</text>
        </view>
        <view
          class="tab"
          :class="{ active: currentTab === 'followers' }"
          @tap="() => switchTab('followers')"
        >
          <text>关注我的</text>
        </view>
      </view>
    </view>

    <!-- 用户列表（我的关注 / 关注我的） -->
    <view v-if="currentTab !== 'likes'" class="content">
      <!-- 加载中 -->
      <view v-if="userLoading && users.length === 0" class="tip">加载中...</view>

      <!-- 空状态 -->
      <view v-else-if="users.length === 0" class="tip">
        <text v-if="currentTab === 'following'">还没有关注任何人，去广场看看吧~</text>
        <text v-else>还没有粉丝，多发点帖子吧~</text>
      </view>

      <!-- 用户列表 -->
      <scroll-view v-else class="list" scroll-y @scrolltolower="loadMore">
        <view v-for="user in users" :key="user.id" class="user-card">
          <view class="user-info" @click="goToProfile(user.id)">
            <UserAvatar :avatar="user.avatar" :anonymous-name="user.anonymous_name" size="medium" />

            <view class="user-details">
              <text class="username">{{ user.anonymous_name }}</text>
              <view class="stats">
                <text class="stat">{{ user.follower_count || 0 }} 粉丝</text>
                <text class="stat">{{ user.post_count || 0 }} 帖子</text>
              </view>
              <text v-if="user.bio" class="bio">{{ user.bio }}</text>
            </view>
          </view>

          <!-- 关注按钮（仅在"我的关注"tab显示） -->
          <view v-if="currentTab === 'following'" class="follow-section" @click.stop>
            <FollowButton
              v-if="authStore.isLoggedIn && user.id !== currentUserId"
              :target-user-id="user.id"
              :is-following="user.is_following ?? true"
              size="small"
              @follow="handleFollow"
              @unfollow="handleUnfollow"
            />
          </view>

          <!-- 互关按钮（在"关注我的"tab显示） -->
          <view v-else class="follow-section" @click.stop>
            <FollowButton
              v-if="authStore.isLoggedIn && user.id !== currentUserId"
              :target-user-id="user.id"
              :is-following="user.is_following ?? false"
              size="small"
              @follow="handleFollow"
              @unfollow="handleUnfollow"
            />
          </view>
        </view>

        <!-- 加载更多 -->
        <view v-if="hasMoreUsers" class="load-more">
          <text v-if="userLoading">加载中...</text>
          <text v-else>加载更多</text>
        </view>
        <view v-else-if="users.length > 0" class="no-more">
          <text>没有更多了</text>
        </view>
      </scroll-view>
    </view>

    <!-- 帖子列表（我的点赞） -->
    <view v-else class="content">
      <!-- 加载中 -->
      <view v-if="postLoading && posts.length === 0" class="tip">加载中...</view>

      <!-- 空状态 -->
      <view v-else-if="posts.length === 0" class="tip">
        <text>还没有点赞任何帖子~</text>
      </view>

      <!-- 帖子列表 -->
      <scroll-view v-else class="list" scroll-y @scrolltolower="loadMore">
        <view v-for="item in posts" :key="item.id" class="card" @click="goDetail(item.id)">
          <view class="row">
            <view class="author-section">
              <UserAvatar
                :avatar="item.user_avatar"
                :anonymous-name="item.anonymous_name"
                size="small"
              />
              <text class="name">{{ item.anonymous_name }}</text>
            </view>
            <text class="time">{{ formatTime(item.created_at) }}</text>
          </view>
          <text class="post-content">{{ item.content }}</text>
          <view v-if="item.images?.length" class="imgs">
            <image
              v-for="(img, i) in item.images.slice(0, 3)"
              :key="i"
              class="thumb"
              :src="img"
              mode="aspectFill"
            />
          </view>
          <view class="post-stats">
            <text class="stat">❤️ {{ item.like_count || 0 }}</text>
            <text class="stat">💬 {{ item.comment_count || 0 }}</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view v-if="hasMorePosts" class="load-more">
          <text v-if="postLoading">加载中...</text>
          <text v-else>加载更多</text>
        </view>
        <view v-else-if="posts.length > 0" class="no-more">
          <text>没有更多了</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: var(--bg-base);
  padding: env(safe-area-inset-top) 0 $spacing-lg;
}

.header {
  background: var(--bg-glass-subtle);
  border-bottom: 1rpx solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
}

.tabs {
  display: flex;
  height: 44px;
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.tab text {
  font-size: $font-size-base;
  color: var(--text-secondary);
}

.tab.active text {
  color: $brand-primary;
  font-weight: $font-weight-semibold;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background-color: $brand-primary;
  border-radius: $radius-xs;
}

.content {
  padding-top: $spacing-lg;
}

.tip {
  padding: 120rpx $spacing-2xl;
  text-align: center;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}

.list {
  height: calc(100vh - 120rpx);
}

/* 用户卡片样式 */
.user-card {
  @include glass-card();
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 $spacing-lg $spacing-lg;
  padding: $spacing-lg;
}

.user-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.user-details {
  flex: 1;
}

.username {
  font-size: $font-size-md;
  font-weight: $font-weight-semibold;
  margin-bottom: $spacing-xs;
  display: block;
}

.stats {
  display: flex;
  gap: $spacing-md;
  margin-top: $spacing-xs;
}

.stat {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.bio {
  font-size: $font-size-xs;
  color: var(--text-secondary);
  margin-top: $spacing-xs;
  display: block;
}

.follow-section {
  margin-left: $spacing-base;
}

/* 帖子卡片样式 */
.card {
  @include glass-card();
  margin: 0 $spacing-lg $spacing-lg;
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
  margin-bottom: $spacing-base;
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

.post-stats {
  display: flex;
  gap: $spacing-xl;
  margin-top: $spacing-base;
}

.post-stats .stat {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.load-more {
  padding: $spacing-lg;
  text-align: center;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}

.no-more {
  padding: $spacing-lg;
  text-align: center;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
</style>
