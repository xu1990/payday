<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  getMyFollowers,
  getUserFollowers,
  getMyFollowing,
  getUserFollowing,
  type UserInfo,
} from '@/api/user'
import { followUser, unfollowUser } from '@/api/user'

const list = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(true)

// 类型: 'followers' | 'following'
const type = ref('followers')
// 目标用户ID（查看其他用户的粉丝/关注时使用）
const targetUserId = ref(null)

async function loadData() {
  loading.value = true
  try {
    if (targetUserId.value) {
      // 查看其他用户
      if (type.value === 'followers') {
        const res = await getUserFollowers(targetUserId.value, {
          limit: pageSize,
          offset: (currentPage.value - 1) * pageSize,
        })
        list.value = res?.items || []
        total.value = res?.total || 0
      } else {
        const res = await getUserFollowing(targetUserId.value, {
          limit: pageSize,
          offset: (currentPage.value - 1) * pageSize,
        })
        list.value = res?.items || []
        total.value = res?.total || 0
      }
    } else {
      // 查看我的
      if (type.value === 'followers') {
        const res = await getMyFollowers({
          limit: pageSize,
          offset: (currentPage.value - 1) * pageSize,
        })
        list.value = res?.items || []
        total.value = res?.total || 0
      } else {
        const res = await getMyFollowing({
          limit: pageSize,
          offset: (currentPage.value - 1) * pageSize,
        })
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

async function handleFollow(user) {
  try {
    await followUser(user.id)
    user.is_following = true
    user.follower_count = (user.follower_count || 0) + 1
    uni.showToast({ title: '关注成功', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

async function handleUnfollow(user) {
  try {
    await unfollowUser(user.id)
    user.is_following = false
    user.follower_count = Math.max((user.follower_count || 1) - 1, 0)
    uni.showToast({ title: '已取消关注', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function goToProfile(user) {
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
          <view v-else class="avatar-placeholder">{{
            user.anonymous_name?.substring(0, 1) || '?'
          }}</view>

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

<style scoped lang="scss">
.follow-page {
  min-height: 100vh;
  background: var(--bg-base);
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-3xl;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}

.user-list {
  padding-bottom: $spacing-sm;
}

.user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: 2rpx;
}

.user-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.avatar,
.avatar-placeholder {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  margin-right: $spacing-sm;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-brand;
  color: #fff;
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
}

.user-details {
  flex: 1;
}

.username {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  margin-bottom: $spacing-xs;
  display: block;
  color: var(--text-primary);
}

.stats {
  display: flex;
  gap: $spacing-lg;
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

.follow-btn {
  margin-left: $spacing-sm;
}

.btn {
  padding: $spacing-xs $spacing-lg;
  background: $gradient-brand;
  border-radius: $radius-sm;
}

.btn text {
  color: #fff;
  font-size: $font-size-xs;
}

.btn.following {
  background: var(--bg-glass-subtle);
}

.btn.following text {
  color: var(--text-secondary);
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

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-3xl;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
</style>
