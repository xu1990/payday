<template>
  <view class="user-list-page">
    <view class="header">
      <text class="title">{{ pageTitle }}</text>
    </view>

    <!-- Tab切换 -->
    <view v-if="!userId" class="tabs">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'followers' }"
        @click="switchTab('followers')"
      >
        <text>粉丝</text>
        <text class="tab-count">{{ followerCount }}</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'following' }"
        @click="switchTab('following')"
      >
        <text>关注</text>
        <text class="tab-count">{{ followingCount }}</text>
      </view>
    </view>

    <!-- 用户列表 -->
    <view v-if="users.length > 0" class="users-list">
      <view v-for="user in users" :key="user.id" class="user-card" @click="viewUser(user.id)">
        <image
          class="user-avatar"
          :src="user.avatar || '/static/default-avatar.png'"
          mode="aspectFill"
        />
        <view class="user-info">
          <text class="user-name">{{ user.anonymous_name }}</text>
          <text v-if="user.bio" class="user-bio">{{ user.bio }}</text>
          <view class="user-stats">
            <text class="stat-item">粉丝：{{ user.follower_count }}</text>
            <text class="stat-item">关注：{{ user.following_count }}</text>
            <text class="stat-item">帖子：{{ user.post_count }}</text>
          </view>
        </view>
        <button
          v-if="userId && activeTab === 'following'"
          class="follow-btn"
          :class="{ following: user.isFollowing }"
          @click.stop="toggleFollow(user)"
        >
          <text>{{ user.isFollowing ? '已关注' : '关注' }}</text>
        </button>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">
      <text class="empty-icon">👥</text>
      <text class="empty-text">暂无{{ activeTab === 'followers' ? '粉丝' : '关注' }}</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getMyFollowers,
  getMyFollowing,
  getUserFollowers,
  getUserFollowing,
  followUser,
  unfollowUser,
  type UserItem,
} from '@/api/follow'

const activeTab = ref('followers')
const users = ref([])
const followerCount = ref(0)
const followingCount = ref(0)
const loading = ref(true)
const userId = ref(null) // 如果有值，则查看某用户的列表

const pageTitle = computed(() => {
  if (userId.value) {
    return activeTab.value === 'followers' ? 'Ta的粉丝' : 'Ta的关注'
  }
  return activeTab.value === 'followers' ? '我的粉丝' : '我的关注'
})

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const options = currentPage.options || {}

  if (options.userId) {
    userId.value = options.userId
  }
  if (options.type) {
    activeTab.value = options.type as 'followers' | 'following'
  }

  loadUsers()
})

const loadUsers = async () => {
  loading.value = true
  try {
    let res
    if (userId.value) {
      // 查看某用户的列表
      if (activeTab.value === 'followers') {
        res = await getUserFollowers(userId.value)
      } else {
        res = await getUserFollowing(userId.value)
      }
    } else {
      // 查看自己的列表
      if (activeTab.value === 'followers') {
        res = await getMyFollowers()
      } else {
        res = await getMyFollowing()
      }
    }
    users.value = res.items
    followerCount.value = activeTab.value === 'followers' ? res.total : 0
    followingCount.value = activeTab.value === 'following' ? res.total : 0
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const switchTab = (tab: 'followers' | 'following') => {
  activeTab.value = tab
  loadUsers()
}

const toggleFollow = async (user) => {
  if (user.allow_follow === 0) {
    uni.showToast({ title: '该用户不允许被关注', icon: 'none' })
    return
  }

  try {
    if (user.isFollowing) {
      await unfollowUser(user.id)
      user.isFollowing = false
      user.follower_count--
    } else {
      await followUser(user.id)
      user.isFollowing = true
      user.follower_count++
    }
  } catch (error) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const viewUser = (userId: string) => {
  uni.navigateTo({ url: `/pages/profile/index?userId=${userId}` })
}
</script>

<style scoped lang="scss">
.user-list-page {
  padding: $spacing-sm;
  background: var(--bg-base);
  min-height: 100vh;
}

.header {
  margin-bottom: $spacing-sm;
}

.title {
  font-size: $font-size-3xl;
  font-weight: $font-weight-bold;
  display: block;
  color: var(--text-primary);
}

.tabs {
  display: flex;
  @include glass-card();
  padding: $spacing-xs;
  margin-bottom: $spacing-lg;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: $spacing-sm;
  border-radius: $radius-md;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}

.tab-item.active {
  background: $gradient-brand;
  color: #fff;
}

.tab-count {
  font-size: $font-size-xs;
  opacity: 0.8;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.user-card {
  display: flex;
  align-items: center;
  @include glass-card();
  padding: $spacing-md;
  position: relative;
}

.user-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  margin-right: $spacing-md;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  display: block;
  margin-bottom: $spacing-xs;
  color: var(--text-primary);
}

.user-bio {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: $spacing-sm;
}

.user-stats {
  display: flex;
  gap: $spacing-sm;
}

.stat-item {
  font-size: $font-size-xs;
  color: var(--text-secondary);
}

.follow-btn {
  width: 120rpx;
  height: 60rpx;
  background: $gradient-brand;
  color: #fff;
  font-size: $font-size-sm;
  border-radius: $radius-xl;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.follow-btn.following {
  background: var(--bg-glass-subtle);
  color: var(--text-secondary);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $spacing-3xl 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: $spacing-sm;
}

.empty-text {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

.loading {
  text-align: center;
  padding: $spacing-xl;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
</style>
