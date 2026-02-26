<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getNotificationList,
  getUnreadCount,
  markRead,
  markOneRead,
  deleteNotifications,
  type NotificationItem,
} from '@/api/notification'
import { formatRelativeTime } from '@/utils/format'

const loading = ref(true)
const errMsg = ref('')
const list = ref([])
const unreadCount = ref(0)
const total = ref(0)
const hasMore = ref(true)
const loadingMore = ref(false)
const limit = 20
let offset = 0

// Flag to prevent duplicate initial fetch (onMounted + onShow both fire on first mount)
const hasMounted = ref(false)

// 类型过滤
type NotificationType = 'all' | 'comment' | 'reply' | 'like' | 'system'
const currentType = ref('all')
const typeTabs: { key; label: string; icon: string }[] = [
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

async function onItemTap(item) {
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
    list.value.forEach(i => (i.is_read = true))
    unreadCount.value = 0
  } catch (_) {}
}

function switchType(type) {
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
    list.value = list.value.filter(item => !selectedIds.value.has(item.id))
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
    success: async res => {
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
  return formatRelativeTime(created_at)
}

onMounted(() => {
  load()
  hasMounted.value = true
})

// Refresh notifications when page is shown (e.g., returning from another page or app wake)
onShow(() => {
  // Skip the first onShow (already called by onMounted)
  if (hasMounted.value) {
    load()
  }
})
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
        <text v-if="!isEditMode" class="action-btn" @click="toggleEditMode"> 管理 </text>
        <template v-else>
          <text class="action-btn cancel" @click="toggleEditMode">取消</text>
          <text v-if="hasSelection" class="action-btn delete" @click="deleteSelected">
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
            <text class="type-badge">{{
              typeTabs.find(t => t.key === item.type)?.icon || '📬'
            }}</text>
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

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: var(--bg-base);
}
.type-tabs {
  display: flex;
  background: var(--bg-glass-standard);
  padding: $spacing-sm $spacing-md;
  gap: $spacing-sm;
  border-bottom: 1rpx solid var(--border-subtle);
}
.type-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm 0;
  border-radius: $radius-md;
  transition: background 0.2s;
}
.type-tab.active {
  background: var(--bg-glass-subtle);
}
.tab-icon {
  font-size: $font-size-lg;
}
.tab-label {
  font-size: $font-size-xs;
  color: var(--text-secondary);
}
.type-tab.active .tab-label {
  color: $brand-primary;
  font-weight: $font-weight-medium;
}
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md;
  background: var(--bg-glass-standard);
  border-bottom: 1rpx solid var(--border-subtle);
}
.action-bar .title {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: var(--text-primary);
}
.actions {
  display: flex;
  gap: $spacing-md;
}
.action-btn {
  font-size: $font-size-sm;
  color: $brand-primary;
}
.action-btn.cancel {
  color: var(--text-secondary);
}
.action-btn.delete {
  color: $semantic-error;
}
.action-btn.danger {
  color: $semantic-error;
}
.loading,
.err,
.empty {
  padding: $spacing-xl;
  text-align: center;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}
.err {
  color: $semantic-error;
}
.list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  padding: $spacing-md;
}
.item {
  @include glass-card();
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
}
.item.unread {
  background: var(--bg-glass-subtle);
}
.item.selected {
  background: var(--bg-glass-subtle);
}
.checkbox {
  display: flex;
  align-items: center;
  padding-top: $spacing-xs;
}
.checkbox-unchecked {
  width: 36rpx;
  height: 36rpx;
  border: 2rpx solid var(--border-regular);
  border-radius: $radius-xs;
}
.checkbox-checked {
  width: 36rpx;
  height: 36rpx;
  background: $brand-primary;
  border-radius: $radius-xs;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: $font-size-xs;
}
.content-wrapper {
  flex: 1;
  min-width: 0;
}
.row {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  margin-bottom: $spacing-xs;
}
.type-badge {
  font-size: $font-size-sm;
}
.item .title {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.time {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.content {
  font-size: $font-size-sm;
  color: var(--text-secondary);
  display: block;
  line-height: 1.5;
}
.load-more {
  padding: $spacing-md;
  text-align: center;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
</style>
