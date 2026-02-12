<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getMyFollowers, getUserFollowers, getMyFollowing, getUserFollowing, type UserInfo } from '@/api/user'
import { followUser, unfollowUser } from '@/api/user'

const list = ref<UserInfo[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(true)

// 类型: 'followers' | 'following'
const type = ref<'followers' | 'following'>('followers')
// 目标用户ID（查看其他用户的粉丝/关注时使用）
const targetUserId = ref<string | null>(null)

async function loadData() {
  loading.value = true
  try {
    if (targetUserId.value) {
      // 查看其他用户
      if (type.value === 'followers') {
        const res = await getUserFollowers(targetUserId.value, { limit: pageSize, offset: (currentPage.value - 1) * pageSize })
        list.value = res?.items || []
        total.value = res?.total || 0
      } else {
        const res = await getUserFollowing(targetUserId.value, { limit: pageSize, offset: (currentPage.value - 1) * pageSize })
        list.value = res?.items || []
        total.value = res?.total || 0
      }
    } else {
      // 查看我的
      if (type.value === 'followers') {
        const res = await getMyFollowers({ limit: pageSize, offset: (currentPage.value - 1) * pageSize })
        list.value = res?.items || []
        total.value = res?.total || 0
      } else {
        const res = await getMyFollowing({ limit: pageSize, offset: (currentPage.value - 1) * pageSize })
        list.value = res?.items || []
        total.value = res?.total || 0
      }
    }
    hasMore.value = list.value.length < total.value
  } catch (e: any) {
    uni.showToast({ title: e?.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  currentPage.value++
  loadData()
}

async function handleFollow(user: UserInfo) {
  try {
    await followUser(user.id)
    user.is_following = true
    user.follower_count = (user.follower_count || 0) + 1
    uni.showToast({ title: '关注成功', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

async function handleUnfollow(user: UserInfo) {
  try {
    await unfollowUser(user.id)
    user.is_following = false
    user.follower_count = Math.max((user.follower_count || 1) - 1, 0)
    uni.showToast({ title: '已取消关注', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function goToProfile(user: UserInfo) {
  uni.navigateTo({
    url: '/pages/profile/index?id=' + user.id,
  })
}

onLoad((options: any) => {
  if (options.type) type.value = options.type
  if (options.userId) targetUserId.value = options.userId
  
  const title = type.value === 'followers' ? '粉丝列表' : '关注列表'
  uni.setNavigationBarTitle({ title })
  
  loadData()
})
</script>

<template>
  <view class="follow-page">
    <view v-if="!loading && list.length === 0" class="empty">
      <text>{{ type === 'followers' ? '暂无粉丝' : '暂无关注' }}</text>
    </view>

    <view v-else class="user-list">
      <view v-for="user in list" :key="user.id" class="user-item" @tap="goToProfile(user)">
        <view class="user-info">
          <image v-if="user.avatar" :src="user.avatar" class="avatar" mode="aspectFill" />
          <view v-else class="avatar-placeholder">{{ user.anonymous_name?.substring(0, 1) || '?' }}</view>
          
          <view class="user-details">
            <text class="username">{{ user.anonymous_name }}</text>
            <view class="stats">
              <text class="stat">{{ user.follower_count || 0 }} 粉丝</text>
              <text class="stat">{{ user.post_count || 0 }} 帖子</text>
            </view>
            <text v-if="user.bio" class="bio">{{ user.bio }}</text>
          </view>
        </view>
        
        <view v-if="targetUserId || type !== 'followers'" class="follow-btn" @tap.stop>
          <view v-if="user.is_following" class="btn following" @tap="handleUnfollow(user)">
            <text>已关注</text>
          </view>
          <view v-else class="btn" @tap="handleFollow(user)">
            <text>关注</text>
          </view>
        </view>
      </view>
      
      <view v-if="hasMore" class="load-more" @tap="loadMore">
        <text v-if="loading">加载中...</text>
        <text v-else>加载更多</text>
      </view>
      <view v-else-if="list.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>
    </view>

    <view v-if="loading && list.length === 0" class="loading-wrapper">
      <text>加载中...</text>
    </view>
  </view>
</template>

<style scoped>
.follow-page { min-height: 100vh; background-color: #f5f5f5; }
.empty { display: flex; align-items: center; justify-content: center; padding: 120rpx; color: #999; }
.user-list { padding-bottom: 20rpx; }
.user-item { display: flex; align-items: center; justify-content: space-between; background-color: #fff; padding: 30rpx; margin-bottom: 2rpx; }
.user-info { display: flex; align-items: center; flex: 1; }
.avatar, .avatar-placeholder { width: 100rpx; height: 100rpx; border-radius: 50%; margin-right: 20rpx; }
.avatar-placeholder { display: flex; align-items: center; justify-content: center; background-color: #07c160; color: #fff; font-size: 18px; font-weight: 600; }
.user-details { flex: 1; }
.username { font-size: 16px; font-weight: 600; margin-bottom: 10rpx; }
.stats { display: flex; gap: 30rpx; margin-top: 8rpx; }
.stat { font-size: 13px; color: #999; }
.bio { font-size: 13px; color: #666; margin-top: 10rpx; }
.follow-btn { margin-left: 20rpx; }
.btn { padding: 10rpx 30rpx; background-color: #07c160; border-radius: 8rpx; }
.btn text { color: #fff; font-size: 13px; }
.btn.following { background-color: #f0f0f0; }
.btn.following text { color: #666; }
.load-more { padding: 30rpx; text-align: center; color: #666; }
.no-more { padding: 30rpx; text-align: center; color: #999; }
.loading-wrapper { display: flex; align-items: center; justify-content: center; padding: 120rpx; color: #999; }
</style>
