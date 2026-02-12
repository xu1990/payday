<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getNotificationList,
  getUnreadCount,
  markRead,
  markOneRead,
  type NotificationItem,
} from '@/api/notification'

const loading = ref(true)
const errMsg = ref('')
const list = ref<NotificationItem[]>([])
const unreadCount = ref(0)
const total = ref(0)
const hasMore = ref(true)
const loadingMore = ref(false)
const limit = 20
let offset = 0

async function loadUnreadCount() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res?.unread_count ?? 0
  } catch {
    unreadCount.value = 0
  }
}

async function load(append = false) {
  if (append) loadingMore.value = true
  else loading.value = true
  errMsg.value = ''
  try {
    const res = await getNotificationList({ limit, offset: append ? offset : 0 })
    const items = res?.items ?? []
    total.value = res?.total ?? 0
    if (append) {
      list.value = list.value.concat(items)
    } else {
      list.value = items
    }
    offset = list.value.length
    hasMore.value = list.value.length < total.value
    await loadUnreadCount()
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    if (!append) list.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  load(true)
}

async function onItemTap(item: NotificationItem) {
  if (!item.is_read) {
    try {
      await markOneRead(item.id)
      item.is_read = true
      if (unreadCount.value > 0) unreadCount.value -= 1
    } catch (_) {}
  }
  if (item.related_id && (item.type === 'comment' || item.type === 'like')) {
    uni.navigateTo({ url: `/pages/post-detail/index?id=${item.related_id}` })
  }
}

async function markAllRead() {
  if (unreadCount.value === 0) return
  try {
    await markRead({ all: true })
    list.value.forEach((i) => (i.is_read = true))
    unreadCount.value = 0
  } catch (_) {}
}

function timeStr(created_at: string) {
  if (!created_at) return ''
  const d = new Date(created_at)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return d.toLocaleDateString()
}

onMounted(() => load())
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">消息</text>
      <text v-if="unreadCount > 0" class="mark-all" @click="markAllRead">全部已读</text>
    </view>

    <view v-if="loading && list.length === 0" class="loading">加载中...</view>
    <view v-else-if="errMsg && list.length === 0" class="err">{{ errMsg }}</view>
    <view v-else-if="list.length === 0" class="empty">暂无消息</view>
    <view v-else class="list">
      <view
        v-for="item in list"
        :key="item.id"
        class="item"
        :class="{ unread: !item.is_read }"
        @click="onItemTap(item)"
      >
        <view class="row">
          <text class="title">{{ item.title }}</text>
          <text class="time">{{ timeStr(item.created_at) }}</text>
        </view>
        <text v-if="item.content" class="content">{{ item.content }}</text>
      </view>
      <view v-if="hasMore" class="load-more" @click="loadMore">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; min-height: 100vh; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.title { font-size: 36rpx; font-weight: 600; }
.mark-all { font-size: 28rpx; color: #07c160; }
.loading, .err, .empty { padding: 48rpx; text-align: center; color: #666; }
.err { color: #e64340; }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.item {
  background: #f8f8f8;
  border-radius: 12rpx;
  padding: 24rpx;
}
.item.unread { background: #f0f9ff; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.item .title { font-size: 30rpx; font-weight: 500; }
.time { font-size: 24rpx; color: #999; }
.content { font-size: 28rpx; color: #666; display: block; }
.load-more { padding: 24rpx; text-align: center; color: #999; font-size: 26rpx; }
</style>
