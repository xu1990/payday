# Square Page Like Button & Follow Feature Design

**Date:** 2025-02-20
**Author:** Claude (AI Assistant)
**Status:** Approved

## Overview

This design implements two feature enhancements for the PayDay mini-program:

1. **Square Page Direct Like:** Add a full action bar (like, comment, share) to post cards on the square page, allowing users to interact without entering the post detail page.

2. **Follow Feature Enhancement:** Add follow/unfollow button to user-home page and make follower/following statistics clickable to navigate to list pages.

## Current State Analysis

### Square Page Issues
- Post cards display like/comment counts but NO interaction buttons
- Users must click into post detail to like posts
- Friction in user experience for quick engagement

### Follow Feature Issues
- Backend follow API exists (`/api/v1/user/{id}/follow`)
- Frontend API wrapper exists (`miniapp/src/api/follow.ts`)
- Generic follower/following list page exists (`miniapp/src/pages/followers/index.vue`)
- **User-home page** shows follower/following counts but:
  - NO follow/unfollow button
  - Counts are NOT clickable (don't navigate to list pages)

## Design Approach

We chose **Component Reuse** approach for:
- DRY principle and consistent UI
- Easier long-term maintenance
- Easy extensibility (e.g., add "save" feature later)
- Better testability

## Architecture

### New Components

#### 1. PostActionBar Component
**Location:** `miniapp/src/components/PostActionBar.vue`

**Props:**
```typescript
interface Props {
  postId: string          // Required: Post ID
  likeCount: number       // Required: Current like count
  commentCount: number    // Required: Current comment count
  viewCount?: number      // Optional: View count (hidden on square page)
  isLiked?: boolean       // Optional: Current like status
  compact?: boolean       // Optional: Compact mode for square page (default: false)
  showView?: boolean      // Optional: Show view count (default: true)
}
```

**Emits:**
```typescript
emit('like', { postId: string, isLiked: boolean })
emit('comment', { postId: string })
emit('share', { postId: string })
```

**Features:**
- Display like, comment, share, view buttons in horizontal row
- Hybrid like behavior: Optimistic update with rollback on error
- Animated like button (heart fills when liked)
- Compact mode reduces padding for square page cards

#### 2. FollowButton Component
**Location:** `miniapp/src/components/FollowButton.vue`

**Props:**
```typescript
interface Props {
  targetUserId: string    // Required: User to follow/unfollow
  isFollowing: boolean    // Required: Current follow status
  size?: 'default' | 'small' | 'large'  // Optional: Button size
}
```

**Emits:**
```typescript
emit('follow', { targetUserId: string })
emit('unfollow', { targetUserId: string })
```

**Features:**
- Displays "关注" or "已关注" button
- Loading state during API call
- Disabled state during API call (prevents double-click)
- Toast messages for success/error feedback

### Modified Pages

#### 1. Square Page (`miniapp/src/pages/square/index.vue`)

**Changes:**
- Import and use `PostActionBar` component
- Add state to track like status for each post
- Remove old static stats display
- Add event handlers for like/comment/share actions

**Template Changes:**
```vue
<!-- OLD (remove) -->
<view class="stats">
  <text>👍 {{ item.like_count }}</text>
  <text>💬 {{ item.comment_count }}</text>
</view>

<!-- NEW -->
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

**State Changes:**
- Add `likedSet: Ref<Set<string>>` to track which posts are liked
- Add `likeLoading: Ref<Set<string>>` to track loading states

#### 2. User-Home Page (`miniapp/src/pages/user-home/index.vue`)

**Changes:**
- Add `FollowButton` component to user stats area
- Make follower/following stats clickable (navigate to list pages)
- Add state to track follow status
- Add API call to check if current user is following target user

**Template Changes:**
```vue
<view class="stats-card">
  <FollowButton
    v-if="!isOwnProfile"
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

**State Changes:**
- Add `isFollowing: Ref<boolean>` to track follow status
- Add `isOwnProfile: Ref<boolean>` to hide button on own profile
- Add `followLoading: Ref<boolean>` for loading state

## Data Flow & Interaction Logic

### Like Action Flow (Hybrid Approach)

```
User clicks like button
  ↓
Immediately update UI (optimistic)
  - Increment/decrement like_count
  - Toggle isLiked state
  - Show brief loading indicator
  ↓
Call API (likePost/unlikePost)
  ↓
If API succeeds → Done (UI already updated)
  ↓
If API fails → Rollback UI
  - Revert like_count
  - Revert isLiked state
  - Show error toast
```

**Key Implementation Details:**
- Use `likedSet` (Set) to track like status per post ID
- Debounce rapid clicks (500ms) to prevent race conditions
- On square page, sync like status with post-detail if user navigates

**Example Implementation:**
```typescript
const likedSet = ref<Set<string>>(new Set())
const likeLoading = ref<Set<string>>(new Set())

async function handleLike(postId: string) {
  if (likeLoading.value.has(postId)) return

  const isLiked = likedSet.value.has(postId)
  const post = list.value.find(p => p.id === postId)
  if (!post) return

  // Optimistic update
  if (isLiked) {
    likedSet.value.delete(postId)
    post.like_count = Math.max(0, post.like_count - 1)
  } else {
    likedSet.value.add(postId)
    post.like_count += 1
  }

  likeLoading.value.add(postId)

  try {
    if (isLiked) {
      await unlikePost(postId)
    } else {
      await likePost(postId)
    }
  } catch {
    // Rollback on error
    if (isLiked) {
      likedSet.value.add(postId)
      post.like_count += 1
    } else {
      likedSet.value.delete(postId)
      post.like_count = Math.max(0, post.like_count - 1)
    }
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    likeLoading.value.delete(postId)
  }
}
```

### Follow Action Flow

```
User clicks follow/unfollow button
  ↓
Show loading state (disable button)
  ↓
Call API (followUser/unfollowUser)
  ↓
If API succeeds:
  - Update isFollowing state
  - Update follower/following counts
  - Show success toast
  ↓
If API fails:
  - Keep isFollowing unchanged
  - Show error toast
  - Re-enable button
```

**Key Implementation Details:**
- Block user action during API call (no optimistic updates)
- Check `allow_follow` permission before showing button
- Hide follow button on own profile page
- Navigate to follower/following list via `uni.navigateTo`

**Navigation Implementation:**
```typescript
function goToFollowerList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=followers&userId=${targetUserId.value}`
  })
}

function goToFollowingList() {
  uni.navigateTo({
    url: `/pages/followers/index?type=following&userId=${targetUserId.value}`
  })
}
```

## Error Handling & Edge Cases

### Error Scenarios

**1. Network Errors**
- Like/Follow API fails → Rollback UI, show error toast
- Timeout after 10 seconds → Show timeout message

**2. Race Conditions**
- Prevent double-click with loading states
- Debounce rapid clicks (500ms)
- Use Set to track loading operations

**3. Edge Cases - Like Feature:**
- User not logged in → Navigate to login page
- Post deleted → Show "帖子不存在" toast
- Like count reaches 0 → Don't decrement below 0

**4. Edge Cases - Follow Feature:**
- Follow self → Hide button (isOwnProfile check)
- Target user disabled follow (`allow_follow=0`) → Hide button
- User already following → Show "已关注" state
- Follower/following count is 0 → Still show "0", allow click

**5. State Persistence:**
- Square page: Like state resets on page reload (acceptable)
- User-home: Follow state loads fresh on mount
- Optional: Cache follow status in localStorage (future enhancement)

### Permission Checks

```typescript
// Follow button visibility
const canFollow = computed(() => {
  return !isOwnProfile.value &&
         targetUser.value?.allow_follow === 1 &&
         authStore.isLoggedIn
})
```

### Loading States

```typescript
// Square page - per-post like loading
const likeLoading = ref<Set<string>>(new Set())

// User-home - single follow loading
const followLoading = ref(false)

// Button disabled state
<button :disabled="followLoading || !canFollow">
```

## Styling

### PostActionBar Styling

**Compact Mode (Square Page):**
```css
.action-bar {
  display: flex;
  gap: 24rpx;
  padding: 16rpx 0;
  font-size: 24rpx;
  color: #666;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  transition: background 0.2s;
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
```

**Full Mode (Post-Detail):**
- Same as current post-detail page styling
- Larger touch targets (32rpx padding)

### FollowButton Styling

```css
.follow-btn {
  padding: 12rpx 32rpx;
  border-radius: 32rpx;
  font-size: 28rpx;
  font-weight: 500;
  transition: all 0.2s;
}

.follow-btn.following {
  background: #f0f0f0;
  color: #666;
}

.follow-btn.not-following {
  background: #07c160;
  color: #fff;
}

.follow-btn:disabled {
  opacity: 0.5;
}

/* Sizes */
.size-small { padding: 8rpx 24rpx; font-size: 24rpx; }
.size-large { padding: 16rpx 40rpx; font-size: 32rpx; }
```

### Clickable Stats (User-Home)

```css
.stat-item {
  cursor: pointer;
  transition: transform 0.1s;
}

.stat-item:active {
  transform: scale(0.95);
}
```

## Testing Considerations

### Unit Tests
- Test `PostActionBar` component emits correct events
- Test `FollowButton` component handles loading states
- Test like/unlike API functions
- Test follow/unfollow API functions

### Integration Tests
- Test square page like action updates UI correctly
- Test user-home page follow action updates state correctly
- Test navigation to follower/following lists

### Edge Case Tests
- Test rapid clicking doesn't cause duplicate API calls
- Test network errors trigger UI rollback
- Test permission checks hide buttons correctly
- Test like count doesn't go below 0

## Files to Create

1. `miniapp/src/components/PostActionBar.vue`
2. `miniapp/src/components/FollowButton.vue`

## Files to Modify

1. `miniapp/src/pages/square/index.vue`
2. `miniapp/src/pages/user-home/index.vue`

## Implementation Checklist

### PostActionBar Component
- [ ] Create component file with props interface
- [ ] Implement like button with hybrid optimistic update
- [ ] Implement comment button (navigates to post detail)
- [ ] Implement share button
- [ ] Add compact mode support
- [ ] Add loading states
- [ ] Add error handling with rollback
- [ ] Add styling (compact and full modes)

### FollowButton Component
- [ ] Create component file with props interface
- [ ] Implement follow/unfollow button
- [ ] Add loading and disabled states
- [ ] Add permission checks
- [ ] Add toast feedback
- [ ] Add styling for different sizes

### Square Page Integration
- [ ] Import and register PostActionBar component
- [ ] Add likedSet and likeLoading state
- [ ] Replace static stats with PostActionBar
- [ ] Implement handleLike function
- [ ] Implement handleComment function
- [ ] Implement handleShare function
- [ ] Add click handler for card (only when not clicking action buttons)

### User-Home Page Integration
- [ ] Import and register FollowButton component
- [ ] Add isFollowing and followLoading state
- [ ] Add isOwnProfile computed property
- [ ] Load follow status on mount
- [ ] Add FollowButton to stats area
- [ ] Make follower count clickable
- [ ] Make following count clickable
- [ ] Implement navigation functions

### Testing
- [ ] Unit tests for PostActionBar
- [ ] Unit tests for FollowButton
- [ ] Integration test for square page like
- [ ] Integration test for user-home follow
- [ ] Manual testing for edge cases

## Summary

This design implements two feature improvements:

1. **Square Page Direct Like:** Full action bar with like, comment, share buttons using hybrid optimistic updates for better UX
2. **Follow Feature Enhancement:** Follow button + clickable stats on user-home page, with navigation to list pages

The component-based approach ensures code reusability and maintainability. Proper error handling and edge case coverage ensure a robust user experience.
