<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyFeed, type FeedPost, type FeedRes } from '@/api/follow'

const list = ref<FeedPost[]>([])
const total = ref(0)
const loading = ref(false)

async function loadFeed() {
  loading.value = true
  try {
    const res = await getMyFeed({ page: 1, page_size: 20 })
    list.value = (res as FeedRes).items ?? []
    total.value = (res as FeedRes).total ?? 0
  } finally {
    loading.value = false
  }
}

onMounted(loadFeed)
</script>

<template>
  <view class="page">
    <text class="title">关注流</text>
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="list.length === 0" class="tip">暂无动态，去关注一些人吧</view>
    <view v-else class="list">
      <view v-for="item in list" :key="item.id" class="item">
        <text class="name">{{ item.anonymous_name }}</text>
        <text class="content">{{ item.content || '（无文字）' }}</text>
        <text class="time">{{ item.created_at }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.title { font-size: 36rpx; font-weight: 600; }
.tip { margin-top: 24rpx; color: #999; font-size: 28rpx; }
.list { margin-top: 24rpx; }
.item { padding: 24rpx 0; border-bottom: 1rpx solid #eee; }
.name { font-weight: 600; margin-right: 16rpx; }
.content { display: block; margin-top: 8rpx; color: #333; }
.time { display: block; margin-top: 8rpx; font-size: 24rpx; color: #999; }
</style>
