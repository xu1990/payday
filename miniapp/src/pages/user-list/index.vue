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

const activeTab = ref<'followers' | 'following'>('followers')
const users = ref<UserItem[]>([])
const followerCount = ref(0)
const followingCount = ref(0)
const loading = ref(true)
const userId = ref<string | null>(null) // 如果有值，则查看某用户的列表

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

const toggleFollow = async (user: UserItem) => {
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

<style scoped>
.user-list-page {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  margin-bottom: 20rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
}

.tabs {
  display: flex;
  background: #fff;
  border-radius: 16rpx;
  padding: 8rpx;
  margin-bottom: 30rpx;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.tab-item.active {
  background: #5470c6;
  color: #fff;
}

.tab-count {
  font-size: 24rpx;
  opacity: 0.8;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.user-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  position: relative;
}

.user-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  margin-right: 24rpx;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 32rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 8rpx;
}

.user-bio {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 12rpx;
}

.user-stats {
  display: flex;
  gap: 20rpx;
}

.stat-item {
  font-size: 24rpx;
  color: #666;
}

.follow-btn {
  width: 120rpx;
  height: 60rpx;
  background: #5470c6;
  color: #fff;
  font-size: 26rpx;
  border-radius: 30rpx;
  border: none;
}

.follow-btn.following {
  background: #f5f5f5;
  color: #666;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.loading {
  text-align: center;
  padding: 40rpx;
  color: #999;
}
</style>
