# Like Status, Follow Buttons, and Notifications Enhancement - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add like status display to posts, follow buttons to square/detail pages, and enhance notifications with entry point and real-time updates.

**Architecture:** Backend adds `is_liked` field to post responses via service layer caching; frontend consumes this data for display and adds follow buttons with batch status checking; notifications enhanced with polling composable and footer navigation entry.

**Tech Stack:** FastAPI (backend), Vue3 Composition API (miniapp), Redis (caching), SQLAlchemy (ORM)

---

## Task 1: Backend - Add `is_liked` Field to PostResponse Schema

**Files:**
- Modify: `backend/app/schemas/post.py`

**Step 1: Read the current PostResponse schema**

```bash
cat backend/app/schemas/post.py
```

**Step 2: Add `is_liked` field to PostResponse**

Edit `backend/app/schemas/post.py`:

```python
class PostResponse(BaseModel):
    id: str
    user_id: str
    anonymous_name: str
    content: str
    images: list[str] | None = None
    tags: list[str] | None = None
    type: str
    salary_range: str | None = None
    industry: str | None = None
    city: str | None = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    status: str = "approved"
    risk_status: str = "pending"
    risk_score: int | None = None
    risk_reason: str | None = None
    created_at: str
    updated_at: str
    # NEW FIELD
    is_liked: bool = False
```

**Step 3: Commit**

```bash
cd backend && git add app/schemas/post.py
git commit -m "feat: add is_liked field to PostResponse schema"
```

---

## Task 2: Backend - Update Post Service to Populate `is_liked`

**Files:**
- Modify: `backend/app/services/post_service.py`
- Test: `backend/tests/test_post_service.py`

**Step 1: Read current post_service.py to understand structure**

```bash
cat backend/app/services/post_service.py
```

**Step 2: Write failing test for `is_liked` in post list**

Create `backend/tests/test_post_service.py` (if not exists) or append:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.post_service import list_posts, get_by_id
from app.models.like import Like
from app.models.post import Post

@pytest.mark.asyncio
async def test_list_posts_includes_is_liked_for_authenticated_user(db: AsyncSession, test_user):
    """Test that list_posts returns is_liked=True for liked posts"""
    # Create a test post
    post = Post(
        id="test-post-1",
        user_id="other-user-id",
        anonymous_name="Anonymous",
        content="Test content",
        status="approved"
    )
    db.add(post)

    # Create a like record
    like = Like(
        user_id=test_user.id,
        target_type="post",
        target_id="test-post-1"
    )
    db.add(like)
    await db.commit()

    # Call list_posts with current_user_id
    posts = await list_posts(db, sort="latest", limit=10, offset=0, current_user_id=test_user.id)

    # Assert is_liked is True for the liked post
    result_posts = [PostResponse.model_validate(p) for p in posts]
    liked_post = next((p for p in result_posts if p.id == "test-post-1"), None)
    assert liked_post is not None
    assert liked_post.is_liked is True
```

**Step 3: Run test to verify it fails**

```bash
cd backend && pytest tests/test_post_service.py::test_list_posts_includes_is_liked_for_authenticated_user -v
```

Expected: FAIL - `list_posts()` doesn't accept `current_user_id` parameter yet

**Step 4: Modify `list_posts()` function to accept and use `current_user_id`**

Edit `backend/app/services/post_service.py`:

```python
async def list_posts(
    db: AsyncSession,
    sort: Literal["hot", "latest"] = "latest",
    limit: int = 20,
    offset: int = 0,
    current_user_id: str | None = None,  # NEW PARAMETER
) -> list[Post]:
    # ... existing query logic ...
    posts = result.scalars().all()

    # NEW: Populate is_liked for authenticated users
    if current_user_id:
        for post in posts:
            post.is_liked = await like_service.is_liked(db, current_user_id, "post", post.id)

    return list(posts)
```

Note: You may need to add `is_liked` as a transient property to the Post model first if it doesn't exist.

**Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/test_post_service.py::test_list_posts_includes_is_liked_for_authenticated_user -v
```

Expected: PASS

**Step 6: Write test for `get_by_id` with `is_liked`**

```python
@pytest.mark.asyncio
async def test_get_by_id_includes_is_liked_for_authenticated_user(db: AsyncSession, test_user):
    """Test that get_by_id returns is_liked=True for liked post"""
    post_id = "test-post-detail-1"
    post = Post(
        id=post_id,
        user_id="other-user-id",
        anonymous_name="Anonymous",
        content="Test content",
        status="approved"
    )
    db.add(post)

    like = Like(
        user_id=test_user.id,
        target_type="post",
        target_id=post_id
    )
    db.add(like)
    await db.commit()

    # Call get_by_id with current_user_id
    result = await get_by_id(db, post_id, current_user_id=test_user.id)

    assert result is not None
    assert result.is_liked is True
```

**Step 7: Update `get_by_id()` function similarly**

Edit `backend/app/services/post_service.py`:

```python
async def get_by_id(
    db: AsyncSession,
    post_id: str,
    only_approved: bool = True,
    increment_view: bool = False,
    current_user_id: str | None = None,  # NEW PARAMETER
) -> Post | None:
    # ... existing logic to fetch post ...

    if post:
        # NEW: Populate is_liked for authenticated users
        if current_user_id:
            post.is_liked = await like_service.is_liked(db, current_user_id, "post", post.id)

    return post
```

**Step 8: Run tests to verify**

```bash
cd backend && pytest tests/test_post_service.py -v
```

Expected: PASS for all tests

**Step 9: Commit**

```bash
cd backend && git add app/services/post_service.py tests/test_post_service.py
git commit -m "feat: populate is_liked field in post service for authenticated users"
```

---

## Task 3: Backend - Update Post Routes to Pass User ID

**Files:**
- Modify: `backend/app/api/v1/post.py`
- Test: `backend/tests/test_api/test_post.py`

**Step 1: Read current post.py routes**

```bash
cat backend/app/api/v1/post.py
```

**Step 2: Update `post_list` endpoint to pass user_id**

Edit `backend/app/api/v1/post.py`:

```python
@router.get("")
async def post_list(
    sort: Literal["hot", "latest"] = Query("latest", description="hot=热门 latest=最新"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),  # CHANGED: make optional
):
    posts = await list_posts(
        db,
        sort=sort,
        limit=limit,
        offset=offset,
        current_user_id=current_user.id if current_user else None  # NEW: pass user_id
    )
    data = [PostResponse.model_validate(p).model_dump(mode='json') for p in posts]
    return success_response(data=data, message="获取帖子列表成功")
```

**Step 3: Update `post_get` endpoint similarly**

```python
@router.get("/{post_id}")
async def post_get(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),  # CHANGED
):
    post = await get_by_id(
        db,
        post_id,
        only_approved=True,
        increment_view=True,
        current_user_id=current_user.id if current_user else None  # NEW
    )
    if not post:
        raise NotFoundException("资源不存在")
    return success_response(data=PostResponse.model_validate(post).model_dump(mode='json'), message="获取帖子详情成功")
```

**Step 4: Create `get_current_user_optional` dependency in deps.py**

Edit `backend/app/core/deps.py`:

```python
async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional authentication - returns None if no valid token"""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except Exception:
        return None

def oauth2_scheme_optional() -> HttpBearer | None:
    """Optional OAuth2 scheme - doesn't raise error if no token"""
    return HttpBearer(auto_error=False)
```

**Step 5: Write integration tests**

Create `backend/tests/integration/test_post_like_status.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.like import Like
from app.models.post import Post
from app.models.user import User

@pytest.mark.asyncio
async def test_post_list_response_includes_is_liked_for_authenticated(async_client, db: AsyncSession, test_user: User):
    """Integration test: POST /api/v1/posts returns is_liked for authenticated users"""
    # Create test post
    post = Post(
        id="integration-post-1",
        user_id="other-user",
        anonymous_name="Other User",
        content="Test post",
        status="approved"
    )
    db.add(post)

    # Create like
    like = Like(
        user_id=test_user.id,
        target_type="post",
        target_id="integration-post-1"
    )
    db.add(like)
    await db.commit()

    # Make authenticated request
    response = await async_client.get(
        "/api/v1/posts?sort=latest&limit=20&offset=0",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    posts = data["data"]
    liked_post = next((p for p in posts if p["id"] == "integration-post-1"), None)
    assert liked_post is not None
    assert liked_post["is_liked"] is True
```

**Step 6: Run tests**

```bash
cd backend && pytest tests/integration/test_post_like_status.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
cd backend && git add app/api/v1/post.py app/core/deps.py tests/integration/test_post_like_status.py
git commit -m "feat: pass current_user_id to post service for is_liked field"
```

---

## Task 4: Backend - Add Batch Follow Status Endpoint

**Files:**
- Create: `backend/app/schemas/follow.py` (if not exists) or modify existing
- Modify: `backend/app/api/v1/follow.py`
- Test: `backend/tests/test_api/test_follow.py`

**Step 1: Read current follow API**

```bash
cat backend/app/api/v1/follow.py
```

**Step 2: Write failing test for batch status endpoint**

```python
@pytest.mark.asyncio
async def test_batch_follow_status_returns_correct_mapping(async_client, test_user: User, db: AsyncSession):
    """Test POST /api/v1/follows/status returns follow status for multiple users"""
    # Setup: follow some users
    target_user_1_id = "target-user-1"
    target_user_2_id = "target-user-2"

    follow1 = Follow(follower_id=test_user.id, following_id=target_user_1_id)
    db.add(follow1)
    await db.commit()

    response = await async_client.post(
        "/api/v1/follows/status",
        json={"user_ids": [target_user_1_id, target_user_2_id]},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"][target_user_1_id] is True
    assert data["data"][target_user_2_id] is False
```

**Step 3: Run test to verify it fails**

```bash
cd backend && pytest tests/test_api/test_follow.py::test_batch_follow_status_returns_correct_mapping -v
```

Expected: FAIL - endpoint doesn't exist

**Step 4: Implement batch status endpoint**

Edit `backend/app/api/v1/follow.py`:

```python
from pydantic import BaseModel
from typing import List

class BatchFollowStatusRequest(BaseModel):
    user_ids: List[str]

@router.post("/status")
async def batch_follow_status(
    body: BatchFollowStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get follow status for multiple users at once"""
    # Validate max 50 IDs
    if len(body.user_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 user IDs allowed")

    # Query all follow relationships in one query
    result = await db.execute(
        select(Follow)
        .where(
            Follow.follower_id == current_user.id,
            Follow.following_id.in_(body.user_ids)
        )
    )
    following_ids = {str(f.following_id) for f in result.scalars().all()}

    # Build response mapping
    status_map = {uid: uid in following_ids for uid in body.user_ids}

    return success_response(data=status_map, message="获取关注状态成功")
```

**Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/test_api/test_follow.py::test_batch_follow_status_returns_correct_mapping -v
```

Expected: PASS

**Step 6: Commit**

```bash
cd backend && git add app/api/v1/follow.py tests/test_api/test_follow.py
git commit -m "feat: add batch follow status endpoint"
```

---

## Task 5: Frontend - Update PostItem Interface

**Files:**
- Modify: `miniapp/src/api/post.ts`

**Step 1: Add `is_liked` field to PostItem interface**

Edit `miniapp/src/api/post.ts`:

```typescript
export interface PostItem {
  id: string
  user_id: string
  anonymous_name: string
  content: string
  images: string[] | null
  tags: string[] | null
  type: string
  salary_range: string | null
  industry: string | null
  city: string | null
  view_count: number
  like_count: number
  comment_count: number
  status: string
  risk_status: string
  risk_score: number | null
  risk_reason: string | null
  created_at: string
  updated_at: string
  // NEW FIELD
  is_liked?: boolean
}
```

**Step 2: Commit**

```bash
cd miniapp && git add src/api/post.ts
git commit -m "feat: add is_liked field to PostItem interface"
```

---

## Task 6: Frontend - Create useNotificationUnread Composable

**Files:**
- Create: `miniapp/src/composables/useNotificationUnread.ts`

**Step 1: Create the composable**

Create `miniapp/src/composables/useNotificationUnread.ts`:

```typescript
import { ref, onUnmounted } from 'vue'
import { getUnreadCount } from '@/api/notification'

const POLL_INTERVAL = 30000 // 30 seconds

export function useNotificationUnread() {
  const unreadCount = ref(0)
  let intervalId: number | null = null

  async function fetch() {
    try {
      const res = await getUnreadCount()
      unreadCount.value = res?.unread_count ?? 0
    } catch (e) {
      console.error('[useNotificationUnread] Failed to fetch unread count:', e)
    }
  }

  function startPolling() {
    fetch() // Initial fetch
    intervalId = setInterval(fetch, POLL_INTERVAL) as unknown as number
  }

  function stopPolling() {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function refresh() {
    fetch()
  }

  // Auto cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    unreadCount,
    startPolling,
    stopPolling,
    refresh,
  }
}
```

**Step 2: Commit**

```bash
cd miniapp && git add src/composables/useNotificationUnread.ts
git commit -m "feat: add useNotificationUnread composable with polling"
```

---

## Task 7: Frontend - Update Square Page for Like Status

**Files:**
- Modify: `miniapp/src/pages/square/index.vue`

**Step 1: Remove likedSet ref and update to use API data**

Edit `miniapp/src/pages/square/index.vue`:

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { getPostList, type PostItem } from '@/api/post'
import { useDebounceFn } from '@/composables/useDebounce'
import { useAuthStore } from '@/stores/auth'
import PostActionBar from '@/components/PostActionBar.vue'
import FollowButton from '@/components/FollowButton.vue'
import { checkFollowStatus } from '@/api/follow'

type Sort = 'hot' | 'latest'
const activeTab = ref<Sort>('hot')
const list = ref<PostItem[]>([])
const followingSet = ref<Set<string>>(new Set()) // NEW: for follow status
const loading = ref(false)
const authStore = useAuthStore()

function formatTime(created_at: string) {
  const d = new Date(created_at)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  return d.toLocaleDateString()
}

async function load() {
  loading.value = true
  try {
    const result = await getPostList({ sort: activeTab.value, limit: 20, offset: 0 })
    console.log('[Square] API returned:', result)
    console.log('[Square] Array length:', Array.isArray(result) ? result.length : 'Not an array')
    list.value = result

    // NEW: Fetch follow status for all authors
    await fetchFollowStatus()
  } catch (error) {
    console.error('[Square] Load failed:', error)
    list.value = []
  } finally {
    loading.value = false
  }
}

// NEW: Fetch follow status for post authors
async function fetchFollowStatus() {
  if (!authStore.isLoggedIn) return

  const authorIds = [...new Set(list.value.map(p => p.user_id))]
  if (authorIds.length === 0) return

  try {
    const statusMap = await checkFollowStatus(authorIds)
    followingSet.value = new Set(
      Object.entries(statusMap)
        .filter(([_, isFollowing]) => isFollowing)
        .map(([userId]) => userId)
    )
  } catch (e) {
    console.error('[Square] Failed to fetch follow status:', e)
  }
}

const { run: debouncedLoad } = useDebounceFn(load, 300)

watch(activeTab, debouncedLoad, { immediate: true })

async function handleLike(data: { postId: string; isLiked: boolean }) {
  const { postId, isLiked } = data
  const post = list.value.find(p => p.id === postId)
  if (!post) return

  // Optimistic update
  if (isLiked) {
    post.is_liked = true
    post.like_count += 1
  } else {
    post.is_liked = false
    post.like_count = Math.max(0, post.like_count - 1)
  }
}

// NEW: Handle follow/unfollow
async function handleFollow(data: { targetUserId: string }) {
  followingSet.value.add(data.targetUserId)
}

async function handleUnfollow(data: { targetUserId: string }) {
  followingSet.value.delete(data.targetUserId)
}

function handleComment(data: { postId: string }) {
  goDetail(data.postId)
}

function handleShare(data: { postId: string }) {
  goDetail(data.postId)
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/post-detail/index?id=${id}` })
}

function goCreate() {
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/login/index' })
    return
  }
  uni.navigateTo({ url: '/pages/post-create/index' })
}
</script>

<template>
  <view class="page">
    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'hot' }" @click="activeTab = 'hot'">
        热门
      </view>
      <view class="tab" :class="{ active: activeTab === 'latest' }" @click="activeTab = 'latest'">
        最新
      </view>
    </view>
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="list.length === 0" class="tip">暂无帖子</view>
    <scroll-view v-else class="list" scroll-y>
      <view v-for="item in list" :key="item.id" class="card" @click="goDetail(item.id)">
        <view class="row">
          <view class="author-section">
            <text class="name">{{ item.anonymous_name }}</text>
            <!-- NEW: Follow button -->
            <FollowButton
              v-if="authStore.isLoggedIn && item.user_id !== authStore.user?.id"
              :target-user-id="item.user_id"
              :is-following="followingSet.has(item.user_id)"
              size="small"
              @follow="handleFollow"
              @unfollow="handleUnfollow"
              @click.stop
            />
          </view>
          <text class="time">{{ formatTime(item.created_at) }}</text>
        </view>
        <text class="content">{{ item.content }}</text>
        <view v-if="item.images?.length" class="imgs">
          <image
            v-for="(img, i) in (item.images || []).slice(0, 3)"
            :key="i"
            class="thumb"
            :src="img"
            mode="aspectFill"
          />
        </view>
        <PostActionBar
          :post-id="item.id"
          :like-count="item.like_count"
          :comment-count="item.comment_count"
          :is-liked="item.is_liked ?? false"
          :compact="true"
          :show-view="false"
          @like="handleLike"
          @comment="handleComment"
          @share="handleShare"
        />
      </view>
    </scroll-view>
    <view class="fab" @click="goCreate">发帖</view>
  </view>
</template>

<style scoped>
/* ... existing styles ... */
.author-section {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
</style>
```

**Step 2: Commit**

```bash
cd miniapp && git add src/pages/square/index.vue
git commit -m "feat: use API is_liked in square page, add follow button to post cards"
```

---

## Task 8: Frontend - Update Post Detail Page for Like Status and Follow Button

**Files:**
- Modify: `miniapp/src/pages/post-detail/index.vue`

**Step 1: Update post detail to use API is_liked and add FollowButton**

Edit `miniapp/src/pages/post-detail/index.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getPostDetail, type PostItem } from '@/api/post'
import { getCommentList, createComment, type CommentItem } from '@/api/comment'
import { likePost, unlikePost } from '@/api/like'
import { likeComment, unlikeComment } from '@/api/like'
import { sanitizePost, isValidImageUrl } from '@/utils/sanitize'
import { useAuthStore } from '@/stores/auth'
import { checkFollowStatus } from '@/api/follow'
import FollowButton from '@/components/FollowButton.vue'

const id = ref('')
const post = ref<PostItem | null>(null)
const loading = ref(true)
const comments = ref<CommentItem[]>([])
const commentLoading = ref(false)
const postLiked = ref(false) // Will be set from API
const commentLikedSet = ref<Set<string>>(new Set())
const replyInput = ref('')
const replyingTo = ref<{ id: string; name: string } | null>(null)
const commentContent = ref('')
const submitLoading = ref(false)
const keyboardHeight = ref(0)
const authStore = useAuthStore()
const isFollowingAuthor = ref(false)

// Computed property for v-model conditional binding
const inputContent = computed({
  get: () => (replyingTo.value ? replyInput.value : commentContent.value),
  set: (value: string) => {
    if (replyingTo.value) {
      replyInput.value = value
    } else {
      commentContent.value = value
    }
  },
})

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

  uni.onKeyboardHeightChange(res => {
    keyboardHeight.value = res.height
  })
})

onUnmounted(() => {
  uni.offKeyboardHeightChange()
})

async function load() {
  loading.value = true
  try {
    post.value = await getPostDetail(id.value)
    // NEW: Use is_liked from API response
    postLiked.value = post.value?.is_liked ?? false

    // NEW: Fetch follow status for post author
    if (post.value?.user_id && authStore.isLoggedIn) {
      try {
        const statusMap = await checkFollowStatus([post.value.user_id])
        isFollowingAuthor.value = statusMap[post.value.user_id] ?? false
      } catch (e) {
        console.error('[PostDetail] Failed to fetch follow status:', e)
      }
    }
  } catch (error) {
    post.value = null
    uni.showToast({ title: '加载帖子失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// ... rest of existing functions ...

// NEW: Handle follow/unfollow
async function handleFollow() {
  isFollowingAuthor.value = true
}

async function handleUnfollow() {
  isFollowingAuthor.value = false
}
</script>

<template>
  <view class="page">
    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="!post" class="tip">帖子不存在</view>
    <view v-else class="card">
      <view class="row">
        <view class="author-section">
          <text class="name">{{ post.anonymous_name }}</text>
          <!-- NEW: Follow button -->
          <FollowButton
            v-if="authStore.isLoggedIn && post.user_id !== authStore.user?.id"
            :target-user-id="post.user_id"
            :is-following="isFollowingAuthor"
            size="small"
            @follow="handleFollow"
            @unfollow="handleUnfollow"
          />
        </view>
        <text class="time">{{ timeStr }}</text>
      </view>
      <!-- ... rest of template ... -->
    </view>
  </view>
</template>

<style scoped>
.author-section {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
</style>
```

**Step 2: Commit**

```bash
cd miniapp && git add src/pages/post-detail/index.vue
git commit -m "feat: use API is_liked in post detail, add follow button"
```

---

## Task 9: Frontend - Add Follow Status API Function

**Files:**
- Modify: `miniapp/src/api/follow.ts`

**Step 1: Add checkFollowStatus function**

Edit `miniapp/src/api/follow.ts`:

```typescript
/**
 * 关注 - 与 backend /api/v1/follows 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/follows'

export interface FollowListResult {
  items: Array<{
    id: string
    follower_id: string
    following_id: string
    created_at: string
  }>
  total: number
}

/** 关注用户 */
export function followUser(userId: string) {
  return request<{ id: string }>({
    url: `${PREFIX}/${userId}`,
    method: 'POST',
  })
}

/** 取消关注用户 */
export function unfollowUser(userId: string) {
  return request<void>({
    url: `${PREFIX}/${userId}`,
    method: 'DELETE',
  })
}

/** 获取关注列表 */
export function getFollowingList(params?: { limit?: number; offset?: number }) {
  const { limit = 20, offset = 0 } = params ?? {}
  return request<FollowListResult>({
    url: `${PREFIX}/following?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

/** 获取粉丝列表 */
export function getFollowerList(params?: { limit?: number; offset?: number }) {
  const { limit = 20, offset = 0 } = params ?? {}
  return request<FollowListResult>({
    url: `${PREFIX}/followers?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

/** NEW: 批量检查关注状态 */
export function checkFollowStatus(userIds: string[]): Promise<Record<string, boolean>> {
  return request<Record<string, boolean>>({
    url: `${PREFIX}/status`,
    method: 'POST',
    data: { user_ids: userIds },
  })
}
```

**Step 2: Commit**

```bash
cd miniapp && git add src/api/follow.ts
git commit -m "feat: add checkFollowStatus batch API function"
```

---

## Task 10: Frontend - Add Notification Tab to AppFooter

**Files:**
- Modify: `miniapp/src/components/AppFooter.vue`

**Step 1: Read current AppFooter**

```bash
cat miniapp/src/components/AppFooter.vue
```

**Step 2: Update AppFooter to include notification tab**

```vue
<script setup lang="ts">
import { useNotificationUnread } from '@/composables/useNotificationUnread'

const activeTab = ref('home')
const { unreadCount, startPolling } = useNotificationUnread()

onMounted(() => {
  startPolling()
})

function switchTab(tab: string) {
  activeTab.value = tab
  if (tab === 'notification') {
    uni.navigateTo({ url: '/pages/notification/list' })
  }
}
</script>

<template>
  <view class="footer">
    <view class="tab" :class="{ active: activeTab === 'home' }" @click="switchTab('home')">
      <text class="icon">🏠</text>
      <text class="label">首页</text>
    </view>
    <view class="tab" :class="{ active: activeTab === 'square' }" @click="switchTab('square')">
      <text class="icon">🏘</text>
      <text class="label">广场</text>
    </view>
    <!-- NEW: Notification tab -->
    <view class="tab" :class="{ active: activeTab === 'notification' }" @click="switchTab('notification')">
      <view class="icon-wrapper">
        <text class="icon">🔔</text>
        <text v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</text>
      </view>
      <text class="label">消息</text>
    </view>
    <view class="tab" :class="{ active: activeTab === 'profile' }" @click="switchTab('profile')">
      <text class="icon">👤</text>
      <text class="label">我的</text>
    </view>
  </view>
</template>

<style scoped>
.footer {
  display: flex;
  justify-content: space-around;
  padding: 12rpx 0;
  padding-bottom: calc(12rpx + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1rpx solid #eee;
}

.tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  flex: 1;
}

.icon-wrapper {
  position: relative;
}

.icon {
  font-size: 44rpx;
}

.label {
  font-size: 22rpx;
  color: #666;
}

.tab.active .label {
  color: #07c160;
  font-weight: 500;
}

.badge {
  position: absolute;
  top: -8rpx;
  right: -12rpx;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  padding: 0 8rpx;
  background: #ff4d4f;
  color: #fff;
  font-size: 20rpx;
  text-align: center;
  border-radius: 16rpx;
}
</style>
```

**Step 3: Commit**

```bash
cd miniapp && git add src/components/AppFooter.vue
git commit -m "feat: add notification tab to AppFooter with unread badge"
```

---

## Task 11: Frontend - Add onShow Refresh to Notification List

**Files:**
- Modify: `miniapp/src/pages/notification/list.vue`

**Step 1: Add onShow lifecycle hook to refresh data**

Edit `miniapp/src/pages/notification/list.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'  // NEW import
import {
  getNotificationList,
  getUnreadCount,
  markRead,
  markOneRead,
  deleteNotifications,
  type NotificationItem,
} from '@/api/notification'

// ... existing code ...

onMounted(() => load())

// NEW: Refresh when page is shown
onShow(() => {
  loadUnreadCount()
  // Optionally reload full list if needed
  // load()
})
</script>
```

**Step 2: Commit**

```bash
cd miniapp && git add src/pages/notification/list.vue
git commit -m "feat: refresh notification unread count on page show"
```

---

## Task 12: Investigation - Check Notification Data

**Files:**
- Backend: `backend/app/services/notification_service.py`
- Test data scripts

**Step 1: Check if notifications are being created**

Read `backend/app/services/notification_service.py` to verify notification creation logic:

```bash
cat backend/app/services/notification_service.py
```

**Step 2: Check like_service to confirm notifications are created on like**

In `backend/app/services/like_service.py`, verify that `notification_service.create_notification` is called when users like posts/comments.

**Step 3: Create test data if needed**

If no notifications exist, create a script to seed test notifications:

Create `backend/scripts/seed_test_notifications.py`:

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.models.notification import Notification
from app.models.user import User
from sqlalchemy import select

async def seed_notifications():
    async with async_session_maker() as db:
        # Get a test user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No users found. Create a user first.")
            return

        notifications = [
            Notification(
                user_id=user.id,
                type="like",
                title="新点赞",
                content="有人赞了你的帖子",
                related_id="test-post-1",
                is_read=False,
            ),
            Notification(
                user_id=user.id,
                type="comment",
                title="新评论",
                content="有人评论了你的帖子",
                related_id="test-post-1",
                is_read=False,
            ),
            Notification(
                user_id=user.id,
                type="system",
                title="系统通知",
                content="欢迎来到薪日 PayDay",
                related_id=None,
                is_read=True,
            ),
        ]

        for notif in notifications:
            db.add(notif)

        await db.commit()
        print(f"Created {len(notifications)} test notifications for user {user.id}")

if __name__ == "__main__":
    asyncio.run(seed_notifications())
```

**Step 4: Run seed script if needed**

```bash
cd backend && python scripts/seed_test_notifications.py
```

**Step 5: Commit if script was created**

```bash
cd backend && git add scripts/seed_test_notifications.py
git commit -m "chore: add test notification seeding script"
```

---

## Task 13: End-to-End Testing

**Files:**
- Manual testing checklist

**Step 1: Test like status in square page**

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start miniapp dev server
3. Open miniapp, navigate to square page
4. Verify posts show correct like status (liked posts are highlighted)
5. Like/unlike posts and verify status updates

**Step 2: Test like status in post detail**

1. Click on a post to view detail
2. Verify the like button shows correct initial state
3. Like/unlike and verify state updates

**Step 3: Test follow buttons**

1. In square page, verify follow buttons appear next to author names (not for own posts)
2. Click follow and verify button changes to "已关注"
3. Unfollow and verify button changes back to "关注"
4. In post detail, verify follow button appears next to author
5. Test follow/unfollow behavior

**Step 4: Test notifications**

1. Verify notification bell icon appears in AppFooter
2. Verify unread count badge shows correct number
3. Click notification tab and verify navigation to list page
4. Create some likes/comments to trigger notifications
5. Verify unread count updates within 30 seconds
6. Navigate away and back - verify onShow refresh works

**Step 5: Test anonymous user behavior**

1. Logout or use anonymous mode
2. Verify `is_liked` is always `false`
3. Verify follow buttons either hidden or prompt login

**Step 6: Fix any bugs found**

Create fix commits as needed.

---

## Task 14: Final Polish and Documentation

**Files:**
- Documentation updates

**Step 1: Update CLAUDE.md if needed**

If there are significant architectural changes, update `CLAUDE.md` with:
- New API endpoints documented
- New composables documented
- Component changes documented

**Step 2: Run all tests**

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd miniapp && npm run test
```

**Step 3: Type checking**

```bash
cd miniapp && npm run type-check
```

**Step 4: Linting**

```bash
# From root
npm run lint:backend
npm run lint:miniapp
```

**Step 5: Final commit**

```bash
git add docs/plans/2026-02-20-like-follow-notification-enhancement.md
git commit -m "docs: add implementation plan for like/follow/notification enhancement"
```

---

## Success Criteria

- [ ] Square page displays correct like status for each post
- [ ] Post detail page displays correct like status
- [ ] Follow buttons appear in square page post cards (not for own posts)
- [ ] Follow buttons appear in post detail page header (not for own posts)
- [ ] Batch follow status API works efficiently
- [ ] Notification tab in AppFooter shows unread count badge
- [ ] Notification list refreshes unread count when page is shown
- [ ] Unread count polls every 30 seconds
- [ ] All tests pass (backend + frontend)
- [ ] Anonymous users see `is_liked=false` and appropriate follow button behavior

---

## Notes

- The `is_liked` field uses the existing cache layer (`LikeCacheService`) for performance
- Follow status is batch-fetched to minimize API calls
- Notification polling uses 30-second interval (configurable in composable)
- Follow buttons use `@click.stop` to prevent triggering post navigation when clicking follow
