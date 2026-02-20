# Like Status, Follow Buttons, and Notifications Enhancement

**Date**: 2026-02-20
**Status**: Approved
**Author**: Claude Code

## Overview

This design addresses 4 issues in the miniapp:
1. Square page needs like status display for each post
2. Post detail page needs like status display
3. No follow button for post authors in square and detail views
4. Notification module lacks entry point and real-time updates

## Architecture Overview & Data Flow

### Backend Changes

**Post Response Enhancement**
- Modify `PostResponse` schema to include `is_liked: bool` field
- Update post service (`post_service.py`) to populate `is_liked` during serialization
- Use the existing `like_service.is_liked()` function which already checks cache first

**Flow:**
1. Client requests `/api/v1/posts` or `/api/v1/posts/{id}`
2. Post service fetches posts from DB
3. For each post, if user is authenticated, call `like_service.is_liked(db, user_id, "post", post_id)`
4. Include result in `is_liked` field of response
5. Cache is automatically handled by `LikeCacheService`

### Frontend Changes

**Like Status Display**
- Update `PostItem` interface to include `is_liked?: boolean`
- Square page: Use `item.is_liked` instead of empty `likedSet`
- Post detail: Use `post.is_liked` for initial state

**Follow Button Integration**
- Add `FollowButton` component to square page cards
- Add `FollowButton` component to post-detail page header
- Both need follow status - requires batch follow status API

**Notification Enhancements**
- Add bell icon badge to `AppFooter` component
- Create composable `useNotificationUnread` for polling/refreshing
- Update notification list page to auto-refresh on `onShow`

## Component Design

### Frontend Components to Modify

**1. PostActionBar Component** (`miniapp/src/components/PostActionBar.vue`)
- Already accepts `isLiked` prop
- No changes needed - parent needs to pass correct `is_liked` value

**2. Square Page** (`miniapp/src/pages/square/index.vue`)
- Remove `likedSet` ref (no longer needed)
- Update template to use `item.is_liked` directly from API
- Add `FollowButton` component to each post card:
  ```vue
  <FollowButton
    v-if="authStore.isLoggedIn && item.user_id !== authStore.user?.id"
    :target-user-id="item.user_id"
    :is-following="followingSet.has(item.user_id)"
    @follow="handleFollow"
    @unfollow="handleUnfollow"
  />
  ```

**3. Post Detail Page** (`miniapp/src/pages/post-detail/index.vue`)
- Change `postLiked` initialization from `false` to use `post.value?.is_liked ?? false`
- Add `FollowButton` to header next to author name:
  ```vue
  <view class="row">
    <text class="name">{{ post.anonymous_name }}</text>
    <FollowButton
      v-if="authStore.isLoggedIn && post.user_id !== authStore.user?.id"
      :target-user-id="post.user_id"
      :is-following="isFollowingAuthor"
      size="small"
      @follow="handleFollow"
      @unfollow="handleUnfollow"
    />
    <text class="time">{{ timeStr }}</text>
  </view>
  ```

**4. AppFooter Component** (`miniapp/src/components/AppFooter.vue`)
- Add notification tab with unread count badge
- Use new `useNotificationUnread` composable

**5. New Composable: `useNotificationUnread`** (`miniapp/src/composables/useNotificationUnread.ts`)
- Fetch unread count on mount
- Refresh every 30 seconds via `setInterval`
- Clear interval on unmount
- Expose `unreadCount` ref and `refresh` function

## API Changes

### Backend API Modifications

**1. Post Schema** (`backend/app/schemas/post.py`)
```python
class PostResponse(BaseModel):
    # ... existing fields ...
    is_liked: bool = False  # NEW: Whether current user liked this post
```

**2. Post Service** (`backend/app/services/post_service.py`)
- Modify `list_posts()` and `get_by_id()` to accept optional `current_user_id` parameter
- When serializing, if `current_user_id` is provided:
  - Call `like_service.is_liked(db, current_user_id, "post", post.id)`
  - Include result in response

**3. Post Routes** (`backend/app/api/v1/post.py`)
- Update `post_list` endpoint to pass `current_user.id` to service if authenticated
- Update `post_get` endpoint similarly
- For anonymous users, `is_liked` will always be `false`

**4. New Follow Route** (`backend/app/api/v1/follow.py`)
- Add `POST /api/v1/follows/status` endpoint
- Accepts `{ "user_ids": ["id1", "id2", ...] }`
- Returns `{ "id1": true, "id2": false, ... }`

### Frontend API Client Updates

**1. Post API** (`miniapp/src/api/post.ts`)
```typescript
export interface PostItem {
  // ... existing fields ...
  is_liked?: boolean  // NEW: Like status for current user
}
```

**2. Follow API Extension** (`miniapp/src/api/follow.ts`)
- Add new function for batch follow status check:
```typescript
export function checkFollowStatus(userIds: string[]) {
  return request<{ [userId: string]: boolean }>({
    url: `${PREFIX}/status`,
    method: 'POST',
    data: { user_ids: userIds }
  })
}
```

## Error Handling & Edge Cases

### Like Status Edge Cases

1. **Anonymous users**: `is_liked` always `false`, no like status check performed
2. **Post with no likes**: `is_liked` is `false`, `like_count` is `0`
3. **Race conditions**: Cache layer (`LikeCacheService`) handles concurrent requests
4. **Service degradation**: If cache fails, fallback to DB query (already implemented in `is_liked()`)

### Follow Button Edge Cases

1. **Own posts**: Don't show follow button when `item.user_id === current_user.id`
2. **Not logged in**: Either hide follow button or show it to prompt login
3. **Anonymous posts**: Use `user_id` from post data (always available)
4. **Follow status fetch failure**: Default to `false` (not following), don't block UI

### Notification Edge Cases

1. **No notifications**: Show empty state with friendly message
2. **API failure**: Display error message, allow retry
3. **Polling failure**: Continue polling, show last known count
4. **Large unread count**: Cap display at "99+" (already implemented in profile page)

### Data Validation

- Validate `user_ids` array in batch follow status API (max 50 IDs per request)
- Validate UUID format for user IDs
- Return `400` for invalid input

## Testing Strategy

### Backend Tests

**1. Post Service Tests** (`tests/test_post_service.py`)
- Test `is_liked` field is `true` when user liked the post
- Test `is_liked` field is `false` when user hasn't liked
- Test `is_liked` is `false` for anonymous users
- Test cache is checked before DB query

**2. Follow API Tests** (`tests/test_follow_api.py`)
- Test batch follow status endpoint returns correct mapping
- Test empty array returns empty object
- Test with invalid user IDs returns 400

**3. Integration Tests**
- Test post list includes `is_liked` for authenticated user
- Test post detail includes `is_liked` for authenticated user
- Test like/unlike then check `is_liked` updates correctly

### Frontend Tests

**1. Component Tests**
- Test `PostActionBar` displays correct like state
- Test `FollowButton` emits correct events
- Test notification badge shows unread count

**2. Page/Integration Tests**
- Test square page displays like status from API
- Test post detail page initializes `postLiked` correctly
- Test follow button appears/disappears based on auth and ownership

**3. Composable Tests**
- Test `useNotificationUnread` fetches on mount
- Test polling interval works correctly
- Test interval is cleaned up on unmount

## Implementation Order

**Phase 1: Backend (Foundation)**
1. Add `is_liked` field to `PostResponse` schema
2. Update post service to populate `is_liked` for authenticated users
3. Add batch follow status endpoint: `POST /api/v1/follows/status`
4. Write backend tests

**Phase 2: Frontend API & Types**
1. Update `PostItem` interface with `is_liked` field
2. Add `checkFollowStatus` function to follow API
3. Create `useNotificationUnread` composable

**Phase 3: Frontend Pages - Like Status**
1. Update square page to use `item.is_liked` from API
2. Update post detail page to use `post.is_liked` for initial state
3. Remove unused `likedSet` ref from square page

**Phase 4: Frontend Pages - Follow Buttons**
1. Add `FollowButton` to square page post cards
2. Add `FollowButton` to post detail page header
3. Implement follow status fetching for authors

**Phase 5: Notifications**
1. Add notification tab to `AppFooter`
2. Add unread count polling via composable
3. Update notification list to refresh on `onShow`

**Phase 6: Investigation & Polish**
1. Investigate why notifications might be empty
2. Add test data seeding if needed
3. End-to-end testing
4. Bug fixes

## Open Questions

1. Should we add the notification tab to AppFooter or use a floating bell icon? (Decision: AppFooter tab is more discoverable)
2. What is the appropriate polling interval for notifications? (Decision: 30 seconds)
3. Should follow status be fetched eagerly or lazily? (Decision: Batch fetch when page loads)

## Related Files

### Backend
- `backend/app/schemas/post.py` - Add `is_liked` field
- `backend/app/services/post_service.py` - Populate `is_liked` in serialization
- `backend/app/api/v1/post.py` - Pass user_id to service
- `backend/app/api/v1/follow.py` - Add batch status endpoint

### Frontend
- `miniapp/src/api/post.ts` - Update PostItem interface
- `miniapp/src/api/follow.ts` - Add checkFollowStatus function
- `miniapp/src/pages/square/index.vue` - Use API is_liked, add FollowButton
- `miniapp/src/pages/post-detail/index.vue` - Use API is_liked, add FollowButton
- `miniapp/src/components/AppFooter.vue` - Add notification tab
- `miniapp/src/composables/useNotificationUnread.ts` - New file
