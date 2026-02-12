<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getNotificationList,
  getUnreadCount,
  markRead,
  markOneRead,
  deleteNotifications,
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

// 类型过滤
type NotificationType = 'all' | 'comment' | 'reply' | 'like' | 'system'
const currentType = ref<NotificationType>('all')
const typeTabs: { key: NotificationType; label: string; icon: string }[] = [
  { key: 'all', label: '全部', icon: '📬' },
  { key: 'comment', label: '评论', icon: '💬' },
  { key: 'reply', label: '回复', icon: '↩️' },
  { key: 'like', label: '点赞', icon: '❤️' },
  { key: 'system', label: '系统', icon: '🔔' },
]

// 批量操作
const isEditMode = ref(false)
const selectedIds = ref<Set<string>>(new Set())
const hasSelection = computed(() => selectedIds.value.size > 0)

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
    const typeFilter = currentType.value === 'all' ? undefined : currentType.value
    const res = await getNotificationList({
      limit,
      offset: append ? offset : 0,
      type_filter: typeFilter,
    })
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
  if (isEditMode.value) {
    toggleSelection(item.id)
    return
  }

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

function switchType(type: NotificationType) {
  if (currentType.value === type) return
  currentType.value = type
  offset = 0
  load()
}

function toggleEditMode() {
  isEditMode.value = !isEditMode.value
  selectedIds.value.clear()
}

function toggleSelection(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

function isSelected(id: string) {
  return selectedIds.value.has(id)
}

async function deleteSelected() {
  if (selectedIds.value.size === 0) return
  try {
    const ids = Array.from(selectedIds.value)
    await deleteNotifications({ notification_ids: ids })
    list.value = list.value.filter((item) => !selectedIds.value.has(item.id))
    total.value -= selectedIds.value.size
    selectedIds.value.clear()
    isEditMode.value = false
    await loadUnreadCount()
  } catch (_) {
    uni.showToast({ title: '删除失败', icon: 'none' })
  }
}

async function deleteAll() {
  uni.showModal({
    title: '确认删除',
    content: '确定要清空所有通知吗？此操作不可恢复。',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteNotifications({ delete_all: true })
          list.value = []
          total.value = 0
          unreadCount.value = 0
          offset = 0
          hasMore.value = false
        } catch (_) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
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
    <!-- 类型标签栏 -->
    <view class="type-tabs">
      <view
        v-for="tab in typeTabs"
        :key="tab.key"
        class="type-tab"
        :class="{ active: currentType === tab.key }"
        @click="switchType(tab.key)"
      >
        <text class="tab-icon">{{ tab.icon }}</text>
        <text class="tab-label">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 操作栏 -->
    <view class="action-bar">
      <text class="title">消息 {{ unreadCount > 0 ? `(${unreadCount})` : '' }}</text>
      <view class="actions">
        <text v-if="!isEditMode" class="action-btn" @click="toggleEditMode">
          管理
        </text>
        <template v-else>
          <text class="action-btn cancel" @click="toggleEditMode">取消</text>
          <text
            v-if="hasSelection"
            class="action-btn delete"
            @click="deleteSelected"
          >
            删除({{ selectedIds.size }})
          </text>
        </template>
        <text v-if="!isEditMode && unreadCount > 0" class="action-btn" @click="markAllRead">
          全部已读
        </text>
        <text v-if="!isEditMode && list.length > 0" class="action-btn danger" @click="deleteAll">
          清空
        </text>
      </view>
    </view>

    <view v-if="loading && list.length === 0" class="loading">加载中...</view>
    <view v-else-if="errMsg && list.length === 0" class="err">{{ errMsg }}</view>
    <view v-else-if="list.length === 0" class="empty">暂无消息</view>
    <view v-else class="list">
      <view
        v-for="item in list"
        :key="item.id"
        class="item"
        :class="{
          unread: !item.is_read,
          selected: isEditMode && isSelected(item.id),
        }"
        @click="onItemTap(item)"
      >
        <view v-if="isEditMode" class="checkbox">
          <view v-if="isSelected(item.id)" class="checkbox-checked">✓</view>
          <view v-else class="checkbox-unchecked"></view>
        </view>
        <view class="content-wrapper">
          <view class="row">
            <text class="type-badge">{{ typeTabs.find(t => t.key === item.type)?.icon || '📬' }}</text>
            <text class="title">{{ item.title }}</text>
            <text class="time">{{ timeStr(item.created_at) }}</text>
          </view>
          <text v-if="item.content" class="content">{{ item.content }}</text>
        </view>
      </view>
      <view v-if="hasMore" class="load-more" @click="loadMore">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
}
.type-tabs {
  display: flex;
  background: #fff;
  padding: 16rpx 24rpx;
  gap: 16rpx;
  border-bottom: 1rpx solid #eee;
}
.type-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 16rpx 0;
  border-radius: 12rpx;
  transition: background 0.2s;
}
.type-tab.active {
  background: #f0f9ff;
}
.tab-icon {
  font-size: 32rpx;
}
.tab-label {
  font-size: 24rpx;
  color: #666;
}
.type-tab.active .tab-label {
  color: #07c160;
  font-weight: 500;
}
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #eee;
}
.title {
  font-size: 32rpx;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 24rpx;
}
.action-btn {
  font-size: 28rpx;
  color: #07c160;
}
.action-btn.cancel {
  color: #666;
}
.action-btn.delete {
  color: #e64340;
}
.action-btn.danger {
  color: #e64340;
}
.loading, .err, .empty {
  padding: 48rpx;
  text-align: center;
  color: #666;
}
.err {
  color: #e64340;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 24rpx;
}
.item {
  display: flex;
  gap: 16rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
}
.item.unread {
  background: #f0f9ff;
}
.item.selected {
  background: #e6f7ff;
}
.checkbox {
  display: flex;
  align-items: center;
  padding-top: 4rpx;
}
.checkbox-unchecked {
  width: 36rpx;
  height: 36rpx;
  border: 2rpx solid #ddd;
  border-radius: 6rpx;
}
.checkbox-checked {
  width: 36rpx;
  height: 36rpx;
  background: #07c160;
  border-radius: 6rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24rpx;
}
.content-wrapper {
  flex: 1;
  min-width: 0;
}
.row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}
.type-badge {
  font-size: 28rpx;
}
.item .title {
  font-size: 30rpx;
  font-weight: 500;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.time {
  font-size: 24rpx;
  color: #999;
  flex-shrink: 0;
}
.content {
  font-size: 28rpx;
  color: #666;
  display: block;
  line-height: 1.5;
}
.load-more {
  padding: 24rpx;
  text-align: center;
  color: #999;
  font-size: 26rpx;
}
</style>
