<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getPostDetail, type PostItem } from '@/api/post'
import {
  getCommentList,
  createComment,
  type CommentItem,
} from '@/api/comment'
import { likePost, unlikePost } from '@/api/like'
import { likeComment, unlikeComment } from '@/api/like'

const id = ref('')
const post = ref<PostItem | null>(null)
const loading = ref(true)
const comments = ref<CommentItem[]>([])
const commentLoading = ref(false)
const postLiked = ref(false)
const commentLikedSet = ref<Set<string>>(new Set())
const replyInput = ref('')
const replyingTo = ref<{ id: string; name: string } | null>(null)
const commentContent = ref('')
const submitLoading = ref(false)
const keyboardHeight = ref(0)

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  id.value = page?.options?.id || ''
  if (id.value) {
    load()
    loadComments()
  } else {
    loading.value = false
  }

  // 监听键盘高度变化，使用响应式变量
  uni.onKeyboardHeightChange((res) => {
    keyboardHeight.value = res.height
  })
})

onUnmounted(() => {
  // 移除键盘监听
  uni.offKeyboardHeightChange()
})

async function load() {
  loading.value = true
  try {
    post.value = await getPostDetail(id.value)
  } catch (error) {
    post.value = null
    uni.showToast({ title: '加载帖子失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  if (!id.value) return
  commentLoading.value = true
  try {
    comments.value = await getCommentList(id.value, { limit: 50, offset: 0 })
  } catch (error) {
    comments.value = []
    uni.showToast({ title: '加载评论失败', icon: 'none' })
  } finally {
    commentLoading.value = false
  }
}

const timeStr = computed(() => {
  if (!post.value?.created_at) return ''
  const d = new Date(post.value.created_at)
  return d.toLocaleString()
})

function commentTime(createdAt: string) {
  const d = new Date(createdAt)
  return d.toLocaleString()
}

async function onPostLike() {
  if (!post.value) return
  try {
    if (postLiked.value) {
      await unlikePost(post.value.id)
      post.value.like_count = Math.max(0, post.value.like_count - 1)
      postLiked.value = false
    } else {
      await likePost(post.value.id)
      post.value.like_count += 1
      postLiked.value = true
    }
  } catch (error) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

async function onCommentLike(c: CommentItem) {
  try {
    const key = c.id
    if (commentLikedSet.value.has(key)) {
      await unlikeComment(key)
      commentLikedSet.value.delete(key)
      c.like_count = Math.max(0, c.like_count - 1)
    } else {
      await likeComment(key)
      commentLikedSet.value.add(key)
      c.like_count += 1
    }
  } catch (error) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function isCommentLiked(c: CommentItem) {
  return commentLikedSet.value.has(c.id)
}

function startReply(c: CommentItem) {
  replyingTo.value = { id: c.id, name: c.anonymous_name }
  replyInput.value = ''
}

function cancelReply() {
  replyingTo.value = null
  replyInput.value = ''
}

async function submitComment() {
  const content = (replyingTo.value ? replyInput.value : commentContent.value).trim()
  if (!content || !post.value || submitLoading.value) return
  submitLoading.value = true
  try {
    await createComment(post.value.id, {
      content,
      parent_id: replyingTo.value?.id ?? undefined,
    })
    commentContent.value = ''
    replyInput.value = ''
    replyingTo.value = null
    post.value.comment_count += 1
    await loadComments()
  } catch (error) {
    uni.showToast({ title: '评论失败', icon: 'none' })
  } finally {
    submitLoading.value = false
  }
}

/**
 * 分享给微信好友
 */
async function shareToWeChat() {
  if (!post.value) return

  try {
    // 使用微信小程序分享功能
    uni.showShareMenu({
      withShareTicket: true,
      fail: (err: any) => {
        uni.showToast({ title: '分享失败', icon: 'none' })
      }
    })
  } catch (error) {
    uni.showToast({ title: '分享失败', icon: 'none' })
  }
}

/**
 * 分享到朋友圈
 * 微信小程序无法直接分享到朋友圈，需要生成海报
 */
async function shareToMoments() {
  if (!post.value) return

  // 跳转到海报生成页面
  uni.navigateTo({
    url: `/pages/poster/index?postId=${post.value.id}`,
    fail: (err: any) => {
      uni.showToast({ title: '跳转失败', icon: 'none' })
    }
  })
}
</script>

<template>
  <view class="page">
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="!post" class="tip">帖子不存在</view>
    <view v-else class="card">
      <view class="row">
        <text class="name">{{ post.anonymous_name }}</text>
        <text class="time">{{ timeStr }}</text>
      </view>
      <text class="content">{{ post.content }}</text>
      <view v-if="post.images?.length" class="imgs">
        <image
          v-for="(img, i) in post.images"
          :key="i"
          class="thumb"
          :src="img"
          mode="widthFix"
        />
      </view>
      <view class="meta">
        <text class="meta-item" @tap="onPostLike">
          {{ postLiked ? '已赞' : '赞' }} {{ post.like_count }}
        </text>
        <text class="meta-item">💬 {{ post.comment_count }}</text>
        <text class="meta-item">👁 {{ post.view_count }}</text>
        <view class="share-actions">
          <button class="share-btn" @tap="shareToWeChat">
            <text class="share-icon">💬</text>
            <text>分享给好友</text>
          </button>
          <button class="share-btn" @tap="shareToMoments">
            <text class="share-icon">⭭</text>
            <text>分享到朋友圈</text>
          </button>
        </view>
      </view>
      <view class="comment-section">
        <view class="comment-title">评论</view>
        <view v-if="commentLoading" class="tip">加载评论中...</view>
        <view v-else-if="!comments.length" class="tip">暂无评论</view>
        <view v-else class="comment-list">
          <view v-for="root in comments" :key="root.id" class="comment-block">
            <view class="comment-row">
              <text class="comment-name">{{ root.anonymous_name }}</text>
              <text class="comment-time">{{ commentTime(root.created_at) }}</text>
            </view>
            <text class="comment-content">{{ root.content }}</text>
            <view class="comment-actions">
              <text
                class="action"
                :class="{ liked: isCommentLiked(root) }"
                @tap="onCommentLike(root)"
              >
                {{ isCommentLiked(root) ? '已赞' : '赞' }} {{ root.like_count }}
              </text>
              <text class="action" @tap="startReply(root)">回复</text>
            </view>
            <view v-if="root.replies?.length" class="replies">
              <view
                v-for="sub in root.replies"
                :key="sub.id"
                class="reply-item"
              >
                <view class="comment-row">
                  <text class="comment-name">{{ sub.anonymous_name }}</text>
                  <text class="comment-time">{{ commentTime(sub.created_at) }}</text>
                </view>
                <text class="comment-content">{{ sub.content }}</text>
                <view class="comment-actions">
                  <text
                    class="action"
                    :class="{ liked: isCommentLiked(sub) }"
                    @tap="onCommentLike(sub)"
                  >
                    {{ isCommentLiked(sub) ? '已赞' : '赞' }} {{ sub.like_count }}
                  </text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
    <!-- 底部发评论 -->
    <view v-if="post" class="bottom-bar" :class="{ 'keyboard-up': keyboardHeight > 0 }">
      <view v-if="replyingTo" class="reply-hint">
        <text>回复 {{ replyingTo.name }}</text>
        <text class="cancel" @tap="cancelReply">取消</text>
      </view>
      <input
        v-model="replyingTo ? replyInput : commentContent"
        class="input"
        placeholder="说点什么..."
        confirm-type="send"
        @confirm="submitComment"
      />
      <button class="btn" :loading="submitLoading" @tap="submitComment">发送</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: #f5f5f5;
}
.tip {
  padding: 48rpx;
  text-align: center;
  color: #999;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.name {
  font-weight: 600;
  font-size: 30rpx;
}
.time {
  font-size: 24rpx;
  color: #999;
}
.content {
  font-size: 30rpx;
  line-height: 1.6;
  color: #333;
  display: block;
}
.imgs {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}
.thumb {
  width: 200rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
}
.meta {
  margin-top: 24rpx;
  font-size: 26rpx;
  color: #999;
}
.meta-item {
  margin-right: 24rpx;
}
.comment-section {
  margin-top: 32rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #eee;
}
.comment-title {
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.comment-block {
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.comment-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 8rpx;
}
.comment-name {
  font-size: 26rpx;
  color: #666;
}
.comment-time {
  font-size: 22rpx;
  color: #999;
}
.comment-content {
  font-size: 28rpx;
  line-height: 1.5;
  color: #333;
  display: block;
  margin-bottom: 12rpx;
}
.comment-actions {
  display: flex;
  gap: 24rpx;
  font-size: 24rpx;
  color: #999;
}
.action {
  padding: 4rpx 0;
}
.action.liked {
  color: #07c160;
}
.replies {
  margin-top: 16rpx;
  padding-left: 24rpx;
  border-left: 4rpx solid #eee;
}
.reply-item {
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f8f8f8;
}
.reply-item:last-child {
  border-bottom: none;
}
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1rpx solid #eee;
  transition: transform 0.3s ease;
}
.bottom-bar.keyboard-up {
  transform: translateY(0);
}
.reply-hint {
  position: absolute;
  left: 24rpx;
  top: -28rpx;
  font-size: 22rpx;
  color: #999;
}
.reply-hint .cancel {
  margin-left: 16rpx;
  color: #07c160;
}
.bottom-bar .input {
  flex: 1;
  height: 64rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  background: #f5f5f5;
  border-radius: 32rpx;
}
.bottom-bar .btn {
  padding: 0 32rpx;
  height: 64rpx;
  line-height: 64rpx;
  font-size: 28rpx;
  background: #07c160;
  color: #fff;
  border-radius: 32rpx;
}
</style>
