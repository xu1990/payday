<template>
  <view class="search-page">
    <view class="search-header">
      <view class="search-bar">
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜索帖子..."
          @confirm="onSearch"
        />
        <button class="search-btn" @click="onSearch">
          <text>🔍</text>
        </button>
      </view>
    </view>

    <!-- 标签筛选 -->
    <view v-if="searchHistory.length > 0 || commonTags.length > 0" class="tags-section">
      <view class="section-title">热门标签</view>
      <view class="tags-list">
        <view
          v-for="tag in commonTags"
          :key="tag"
          class="tag-item"
          :class="{ active: selectedTags.includes(tag) }"
          @click="toggleTag(tag)"
        >
          <text class="tag-text">#{{ tag }}</text>
        </view>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view v-if="hasSearched" class="results-section">
      <view class="results-header">
        <text class="results-count">找到 {{ results.length }} 个结果</text>
        <view class="sort-tabs">
          <view class="sort-tab" :class="{ active: sortBy === 'hot' }" @click="sortBy = 'hot'">
            <text>热门</text>
          </view>
          <view
            class="sort-tab"
            :class="{ active: sortBy === 'latest' }"
            @click="sortBy = 'latest'"
          >
            <text>最新</text>
          </view>
        </view>
      </view>

      <view class="posts-list">
        <view v-for="post in results" :key="post.id" class="post-card" @click="viewPost(post.id)">
          <view class="post-header">
            <view class="author-section">
              <UserAvatar
                :avatar="post.user_avatar"
                :anonymous-name="post.anonymous_name"
                size="small"
              />
              <text class="name">{{ post.anonymous_name }}</text>
            </view>
            <text class="post-time">{{ formatTime(post.created_at) }}</text>
            <view v-if="post.type" class="post-tag">
              <text>{{ getTypeText(post.type) }}</text>
            </view>
          </view>
          <view class="post-content">
            <text class="content-text">{{ post.content }}</text>
          </view>
          <view v-if="post.images && post.images.length > 0" class="post-images">
            <image
              v-for="(img, index) in post.images.slice(0, 3)"
              :key="index"
              :src="img"
              mode="aspectFill"
              class="post-image"
            />
          </view>
          <view class="post-footer">
            <view class="footer-stats">
              <text class="stat-item">👁 {{ post.view_count }}</text>
              <text class="stat-item">❤️ {{ post.like_count }}</text>
              <text class="stat-item">💬 {{ post.comment_count }}</text>
            </view>
            <view v-if="post.tags && post.tags.length > 0" class="post-tags">
              <text v-for="(tag, index) in post.tags.slice(0, 3)" :key="index" class="footer-tag">
                #{{ tag }}
              </text>
              <text v-if="post.tags.length > 3" class="more-tags">
                +{{ post.tags.length - 3 }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <!-- 加载更多 -->
      <view v-if="hasMore && !loading" class="load-more" @click="loadMore">
        <text>加载更多</text>
      </view>

      <!-- 空状态 -->
      <view v-if="!hasSearched && !loading" class="empty">
        <text class="empty-icon">🔍</text>
        <text class="empty-text">搜索帖子内容、标签或用户</text>
      </view>

      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { searchPosts } from '@/api/search'
import UserAvatar from '@/components/UserAvatar.vue'

const keyword = ref('')
const selectedTags = ref([])
const sortBy = ref('hot')
const results = ref([])
const hasSearched = ref(false)
const loading = ref(false)
const hasMore = ref(false)
const offset = ref(0)
const limit = 20

const commonTags = ref(['找工作', '工资拖欠', '加班', '年终奖', '离职', '吐槽', '分享'])
const searchHistory = ref([])

onMounted(() => {
  const savedHistory = uni.getStorageSync('search_history') || '[]'
  searchHistory.value = JSON.parse(savedHistory)
})

const onSearch = () => {
  if (!keyword.value.trim()) {
    uni.showToast({ title: '请输入搜索内容', icon: 'none' })
    return
  }

  // 保存到历史记录
  const history = [keyword.value, ...searchHistory.value].slice(0, 9)
  uni.setStorageSync('search_history', JSON.stringify(history))
  searchHistory.value = history

  performSearch()
}

const performSearch = async () => {
  loading.value = true
  offset.value = 0
  hasMore.value = false

  try {
    const data = await searchPosts({
      keyword: keyword.value,
      tags: selectedTags.value.length > 0 ? selectedTags.value : undefined,
      sort: sortBy.value,
      limit: limit,
    })
    results.value = data.items
    hasSearched.value = true
    hasMore.value = data.items.length === limit
  } catch (error) {
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const toggleTag = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
  // 重新搜索
  performSearch()
}

const loadMore = () => {
  offset.value += limit
  performSearch()
}

const viewPost = (postId: string) => {
  uni.navigateTo({ url: `/pages/post-detail/index?id=${postId}` })
}

const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else {
    return '刚刚'
  }
}

const getTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    complaint: '吐槽',
    sharing: '分享',
    question: '提问',
  }
  return typeMap[type] || '帖子'
}
</script>

<style scoped lang="scss">
.search-page {
  padding: $spacing-md;
  background: var(--bg-base);
  min-height: 100vh;
}

.search-header {
  margin-bottom: $spacing-md;
}

.search-bar {
  @include glass-card();
  display: flex;
  gap: $spacing-md;
  padding: $spacing-md;
}

.search-input {
  @include glass-input();
  flex: 1;
  height: 72rpx;
  padding: 0 $spacing-md;
  font-size: $font-size-sm;
  border-radius: $radius-sm;
}

.search-btn {
  width: 80rpx;
  height: 72rpx;
  background: $brand-primary;
  color: #fff;
  border: none;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tags-section {
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  margin-bottom: $spacing-sm;
  color: var(--text-primary);
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.tag-item {
  padding: $spacing-xs $spacing-md;
  background: var(--bg-glass-subtle);
  border: 2rpx solid var(--border-regular);
  border-radius: $radius-full;
}

.tag-item.active {
  background: $brand-primary;
  color: #fff;
  border-color: $brand-primary;
}

.tag-text {
  font-size: $font-size-sm;
}

.results-section {
  margin-top: $spacing-md;
}

.results-header {
  @include glass-card();
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md;
  margin-bottom: $spacing-md;
}

.results-count {
  font-size: $font-size-sm;
  color: var(--text-secondary);
}

.sort-tabs {
  display: flex;
  gap: $spacing-md;
}

.sort-tab {
  padding: $spacing-xs $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-sm;
  font-size: $font-size-sm;
}

.sort-tab.active {
  background: $brand-primary;
  color: #fff;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.post-card {
  @include glass-card();
  padding: $spacing-md;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-sm;
}

.author-section {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
}

.name {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
}

.post-time {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.post-tag {
  padding: $spacing-xs $spacing-sm;
  background: var(--bg-glass-subtle);
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: var(--text-secondary);
}

.post-content {
  font-size: $font-size-sm;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: $spacing-sm;
}

.post-images {
  display: flex;
  gap: $spacing-xs;
  margin-bottom: $spacing-sm;
}

.post-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: $radius-md;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: $spacing-sm;
}

.footer-stats {
  display: flex;
  gap: $spacing-md;
}

.stat-item {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.post-tags {
  display: flex;
  gap: $spacing-xs;
  flex-wrap: wrap;
}

.footer-tag {
  padding: $spacing-xs $spacing-sm;
  background: var(--bg-glass-subtle);
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: $brand-primary;
}

.more-tags {
  font-size: $font-size-xs;
  color: $brand-primary;
}

.load-more {
  text-align: center;
  padding: $spacing-lg;
  @include glass-card();
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: $spacing-md;
}

.empty-text {
  font-size: $font-size-sm;
  color: var(--text-tertiary);
}

.loading {
  text-align: center;
  padding: $spacing-lg;
  color: var(--text-tertiary);
  font-size: $font-size-sm;
}
</style>
