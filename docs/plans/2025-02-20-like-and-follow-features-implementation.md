# Square Page Like Button & Follow Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add direct like button to square page post cards and follow button with clickable stats to user-home page

**Architecture:** Component-based approach with reusable PostActionBar and FollowButton components. Square page uses hybrid optimistic updates for likes, user-home uses blocking approach for follows.

**Tech Stack:** Vue3 Composition API, TypeScript, uni-app, existing like/follow APIs

---

## Task 1: Create PostActionBar Component (Scaffold)

**Files:**
- Create: `miniapp/src/components/PostActionBar.vue`

**Step 1: Create component file with basic structure**

Create the component file:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  postId: string
  likeCount: number
  commentCount: number
  viewCount?: number
  isLiked?: boolean
  compact?: boolean
  showView?: boolean
}

interface Emits {
  (e: 'like', data: { postId: string; isLiked: boolean }): void
  (e: 'comment', data: { postId: string }): void
  (e: 'share', data: { postId: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  viewCount: 0,
  isLiked: false,
  compact: false,
  showView: true,
})

const emit = defineEmits<Emits>()

const likeLoading = ref(false)

function handleLike() {
  if (likeLoading.value) return
  emit('like', { postId: props.postId, isLiked: props.isLiked || false })
}

function handleComment() {
  emit('comment', { postId: props.postId })
}

function handleShare() {
  emit('share', { postId: props.postId })
}
</script>

<template>
  <view class="action-bar" :class="{ compact }">
    <view
      class="action-btn"
      :class="{ liked: isLiked, loading: likeLoading }"
      @tap="handleLike"
    >
      <text class="icon">{{ isLiked ? '❤️' : '🤍' }}</text>
      <text class="count">{{ likeCount }}</text>
    </view>
    <view class="action-btn" @tap="handleComment">
      <text class="icon">💬</text>
      <text class="count">{{ commentCount }}</text>
    </view>
    <view v-if="showView && viewCount > 0" class="action-btn">
      <text class="icon">👁</text>
      <text class="count">{{ viewCount }}</text>
    </view>
    <view class="action-btn" @tap="handleShare">
      <text class="icon">⤴</text>
    </view>
  </view>
</template>

<style scoped>
.action-bar {
  display: flex;
  gap: 24rpx;
  padding: 16rpx 0;
  font-size: 24rpx;
  color: #666;
}

.action-bar.compact {
  padding: 12rpx 0;
  gap: 20rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  transition: background 0.2s;
}

.action-bar.compact .action-btn {
  padding: 6rpx 12rpx;
}

.action-btn:active {
  background: #f0f0f0;
}

.action-btn.liked {
  color: #ff4757;
}

.action-btn.loading {
  opacity: 0.5;
}

.icon {
  font-size: 28rpx;
}

.count {
  font-size: 24rpx;
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/PostActionBar.vue
git commit -m "feat: scaffold PostActionBar component"
```

---

## Task 2: Add Like Logic to PostActionBar

**Files:**
- Modify: `miniapp/src/components/PostActionBar.vue`

**Step 1: Import like API**

Add import at the top of script section:

```typescript
import { ref, computed } from 'vue'
import { likePost, unlikePost } from '@/api/like'
```

**Step 2: Implement internal like handling**

Replace the handleLike function with:

```typescript
async function handleLike() {
  if (likeLoading.value) return

  const currentlyLiked = props.isLiked || false
  const newLikedState = !currentlyLiked

  // Emit event with optimistic state
  likeLoading.value = true
  emit('like', { postId: props.postId, isLiked: newLikedState })

  try {
    if (newLikedState) {
      await likePost(props.postId)
    } else {
      await unlikePost(props.postId)
    }
  } catch (error) {
    // Emit rollback event on failure
    emit('like', { postId: props.postId, isLiked: currentlyLiked })
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    likeLoading.value = false
  }
}
```

**Step 3: Commit**

```bash
git add miniapp/src/components/PostActionBar.vue
git commit -m "feat: add like logic to PostActionBar with optimistic updates"
```

---

## Task 3: Create FollowButton Component

**Files:**
- Create: `miniapp/src/components/FollowButton.vue`

**Step 1: Create component file**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { followUser, unfollowUser } from '@/api/follow'

interface Props {
  targetUserId: string
  isFollowing: boolean
  size?: 'default' | 'small' | 'large'
}

interface Emits {
  (e: 'follow', data: { targetUserId: string }): void
  (e: 'unfollow', data: { targetUserId: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
})

const emit = defineEmits<Emits>()
const loading = ref(false)

async function handleClick() {
  if (loading.value) return

  loading.value = true
  try {
    if (props.isFollowing) {
      await unfollowUser(props.targetUserId)
      emit('unfollow', { targetUserId: props.targetUserId })
      uni.showToast({ title: '已取消关注', icon: 'success' })
    } else {
      await followUser(props.targetUserId)
      emit('follow', { targetUserId: props.targetUserId })
      uni.showToast({ title: '关注成功', icon: 'success' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '操作失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view
    class="follow-btn"
    :class="[size, { following: isFollowing, loading }]"
    @tap="handleClick"
  >
    <text v-if="loading">加载中</text>
    <text v-else>{{ isFollowing ? '已关注' : '关注' }}</text>
  </view>
</template>

<style scoped>
.follow-btn {
  padding: 12rpx 32rpx;
  border-radius: 32rpx;
  font-size: 28rpx;
  font-weight: 500;
  background: #07c160;
  color: #fff;
  transition: all 0.2s;
}

.follow-btn.following {
  background: #f0f0f0;
  color: #666;
}

.follow-btn:disabled {
  opacity: 0.5;
}

.follow-btn.small {
  padding: 8rpx 24rpx;
  font-size: 24rpx;
}

.follow-btn.large {
  padding: 16rpx 40rpx;
  font-size: 32rpx;
}
</style>
```

**Step 2: Commit**

```bash
git add miniapp/src/components/FollowButton.vue
git commit -m "feat: add FollowButton component"
```

---

## Task 4: Update Square Page to Use PostActionBar

**Files:**
- Modify: `miniapp/src/pages/square/index.vue`

**Step 1: Import PostActionBar component**

Add at the top of the script section:

```typescript
import { ref, watch } from 'vue'
import { getPostList, type PostItem } from '@/api/post'
import { useDebounceFn } from '@/composables/useDebounce'
import { useAuthStore } from '@/stores/auth'
import PostActionBar from '@/components/PostActionBar.vue'
```

**Step 2: Add state for tracking likes**

Add after the `list` ref:

```typescript
const list = ref<PostItem[]>([])
const likedSet = ref<Set<string>>(new Set())
const likeLoading = ref<Set<string>>(new Set())
```

**Step 3: Add like handler function**

Add before the `goDetail` function:

```typescript
async function handleLike(data: { postId: string; isLiked: boolean }) {
  const { postId, isLiked } = data
  if (likeLoading.value.has(postId)) return

  const post = list.value.find(p => p.id === postId)
  if (!post) return

  // Optimistic update
  if (isLiked) {
    likedSet.value.add(postId)
    post.like_count += 1
  } else {
    likedSet.value.delete(postId)
    post.like_count = Math.max(0, post.like_count - 1)
  }
}
```

**Step 4: Add comment and share handlers**

Add after the `handleLike` function:

```typescript
function handleComment(data: { postId: string }) {
  goDetail(data.postId)
}

function handleShare(data: { postId: string }) {
  goDetail(data.postId)
}
```

**Step 5: Update template to use PostActionBar**

Replace the stats section in the template:

```vue
<!-- OLD (remove this) -->
<view class="stats">
  <text>👍 {{ item.like_count }}</text>
  <text>💬 {{ item.comment_count }}</text>
</view>

<!-- NEW (add this) -->
<PostActionBar
  :post-id="item.id"
  :like-count="item.like_count"
  :comment-count="item.comment_count"
  :is-liked="likedSet.has(item.id)"
  :compact="true"
  :show-view="false"
  @like="handleLike"
  @comment="handleComment"
  @share="handleShare"
/>
```

**Step 6: Remove old stats CSS**

Remove the `.stats` CSS class:

```css
/* Remove this section */
.stats {
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #999;
}
.stats text {
  margin-right: 24rpx;
}
```

**Step 7: Commit**

```bash
git add miniapp/src/pages/square/index.vue
git commit -m "feat: add PostActionBar to square page with direct like functionality"
```

---

## Task 5: Update User-Home Page - Add Follow Button

**Files:**
- Modify: `miniapp/src/pages/user-home/index.vue`

**Step 1: Import FollowButton and auth store**

Add imports at the top:

```typescript
import { ref, onMounted, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getPostList, type PostItem } from '@/api/post'
import { getCheckinList, type CheckinItem } from '@/api/checkin'
import { useAuthStore } from '@/stores/auth'
import FollowButton from '@/components/FollowButton.vue'
```

**Step 2: Add auth store reference**

Add after the targetUserId ref:

```typescript
const targetUserId = ref('')
const authStore = useAuthStore()
```

**Step 3: Add follow state**

Add after the checkinPage ref:

```typescript
const hasMore = ref(true)
const loadingMore = ref(false)
const isFollowing = ref(false)
const followLoading = ref(false)
```

**Step 4: Add isOwnProfile computed**

Add after the followLoading ref:

```typescript
const isOwnProfile = computed(() => {
  return authStore.user?.id === targetUserId.value
})
```

**Step 5: Add follow status check function**

Add before the `loadProfileData` function:

```typescript
async function checkFollowStatus() {
  if (isOwnProfile.value) return

  try {
    const result = await uni.request({
      url: `/api/v1/user/${targetUserId.value}/follow-status`,
      method: 'GET',
    })
    isFollowing.value = result.data?.is_following || false
  } catch (e) {
    // Ignore error, default to not following
  }
}
```

**Step 6: Add follow/unfollow handlers**

Add before the `switchTab` function:

```typescript
async function handleFollow() {
  if (followLoading.value) return

  followLoading.value = true
  try {
    await uni.request({
      url: `/api/v1/user/${targetUserId.value}/follow`,
      method: 'POST',
    })
    isFollowing.value = true
    followerCount.value += 1
    uni.showToast({ title: '关注成功', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  } finally {
    followLoading.value = false
  }
}

async function handleUnfollow() {
  if (followLoading.value) return

  followLoading.value = true
  try {
    await uni.request({
      url: `/api/v1/user/${targetUserId.value}/follow`,
      method: 'DELETE',
    })
    isFollowing.value = false
    followerCount.value = Math.max(0, followerCount.value - 1)
    uni.showToast({ title: '已取消关注', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  } finally {
    followLoading.value = false
  }
}
```

**Step 7: Update loadProfileData to check follow status**

Modify the loadProfileData function, add at the end of try block:

```typescript
async function loadProfileData() {
  loading.value = true
  try {
    // ... existing code ...

    // Add this at the end of try block
    await checkFollowStatus()
  } catch (e) {
    // Failed to load user profile
  } finally {
    loading.value = false
  }
}
```

**Step 8: Add FollowButton to template**

Replace the stats-card section in template:

```vue
<!-- OLD -->
<view class="stats-card">
  <view class="stat-item">
    <text class="stat-value">{{ followerCount }}</text>
    <text class="stat-label">粉丝</text>
  </view>
  <view class="stat-item">
    <text class="stat-value">{{ followingCount }}</text>
    <text class="stat-label">关注</text>
  </view>
</view>

<!-- NEW -->
<view class="stats-card">
  <FollowButton
    v-if="!isOwnProfile && authStore.isLoggedIn"
    :target-user-id="targetUserId"
    :is-following="isFollowing"
    @follow="handleFollow"
    @unfollow="handleUnfollow"
  />
  <view class="stat-item" @tap="goToFollowerList">
    <text class="stat-value">{{ followerCount }}</text>
    <text class="stat-label">粉丝</text>
  </view>
  <view class="stat-item" @tap="goToFollowingList">
    <text class="stat-value">{{ followingCount }}</text>
    <text class="stat-label">关注</text>
  </view>
</view>
```

**Step 9: Add navigation handlers**

Add after the `formatDate` function:

```typescript
function goToFollowerList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=followers&userId=${targetUserId.value}`,
  })
}

function goToFollowingList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=following&userId=${targetUserId.value}`,
  })
}
```

**Step 10: Add clickable stats styling**

Add to the `.stat-item` CSS:

```css
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  cursor: pointer;
  transition: transform 0.1s;
}

.stat-item:active {
  transform: scale(0.95);
}
```

**Step 11: Commit**

```bash
git add miniapp/src/pages/user-home/index.vue
git commit -m "feat: add FollowButton and clickable stats to user-home page"
```

---

## Task 6: Add Follow Status API Endpoint (Backend)

**Files:**
- Create: `backend/app/api/v1/user.py` (modify if exists)

**Step 1: Add follow status endpoint**

Add this endpoint to the user router:

```python
@router.get("/{user_id}/follow-status")
async def check_follow_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if current user is following target user."""
    if not await get_user_by_id(db, user_id):
        raise NotFoundException("资源不存在")

    following = await is_following(db, current_user.id, user_id)
    return success_response(data={"is_following": following}, message="获取关注状态成功")
```

**Step 2: Commit**

```bash
git add backend/app/api/v1/user.py
git commit -m "feat: add follow status check endpoint"
```

---

## Task 7: Manual Testing

**Files:**
- Test: Manual testing in WeChat DevTools

**Step 1: Test square page like functionality**

1. Start the miniapp in WeChat DevTools
2. Navigate to square page
3. Click like button on a post card
4. Verify:
   - Like count increments immediately
   - Heart icon fills
   - No navigation to detail page
5. Click like button again
6. Verify:
   - Like count decrements
   - Heart icon unfills
7. Click comment button
8. Verify navigates to post detail

**Step 2: Test user-home follow functionality**

1. Navigate to another user's profile (not your own)
2. Verify follow button shows "关注"
3. Click follow button
4. Verify:
   - Button shows loading state
   - Button changes to "已关注"
   - Follower count increments
   - Success toast appears
5. Click "已关注" button
6. Verify:
   - Button shows loading state
   - Button changes to "关注"
   - Follower count decrements
7. Click on follower count
8. Verify navigates to follower list page
9. Click on following count
10. Verify navigates to following list page

**Step 3: Test error handling**

1. Turn off network connection
2. Try to like a post
3. Verify error toast appears and UI rolls back
4. Try to follow a user
5. Verify error toast appears

**Step 4: Document test results**

Create test notes in project notes or issue tracker.

---

## Task 8: Final Verification

**Files:**
- Verify: All modified files

**Step 1: Run linters**

```bash
cd /Users/a1234/Documents/workspace/payDay
npm run lint:miniapp
npm run format:miniapp
```

**Step 2: Run type checks**

```bash
cd miniapp
npm run type-check
```

**Step 3: Verify all tests pass**

```bash
cd /Users/a1234/Documents/workspace/payDay
npm run test:miniapp
```

**Step 4: Final commit with completed implementation**

```bash
git add .
git commit -m "feat: complete square page like and user-home follow features

- Add PostActionBar component with optimistic like updates
- Add FollowButton component with loading states
- Update square page to use PostActionBar for direct likes
- Update user-home page with FollowButton and clickable stats
- Add follow status check endpoint to backend

All features tested and working."
```

---

## Implementation Notes

### Key Design Decisions

1. **Hybrid approach for likes**: Optimistic UI update with rollback on error provides fast UX while maintaining data consistency

2. **Blocking approach for follows**: No optimistic updates because follow status affects permission checks

3. **Component reusability**: PostActionBar and FollowButton can be reused in feed page and other locations

4. **State management**: Using local state (ref) instead of global store to keep components self-contained

### API Dependencies

- `/api/v1/posts/{id}/like` - POST for like, DELETE for unlike
- `/api/v1/user/{id}/follow` - POST for follow, DELETE for unfollow
- `/api/v1/user/{id}/follow-status` - GET to check follow status (new endpoint)

### Testing Strategy

- Manual testing recommended for UI components
- Unit tests can be added later for component logic
- Integration tests for API endpoints

### Future Enhancements

- Add "save to collection" button to PostActionBar
- Cache follow status in localStorage for faster page loads
- Add follow button to user mentions in comments
- Add share functionality to PostActionBar
