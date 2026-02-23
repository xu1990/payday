# 用户头像显示功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在小程序端的广场列表、帖子详情、我的关注/点赞页面中添加用户头像显示，采用冗余存储方案实现。

**Architecture:** 在 `posts` 表添加 `user_avatar` 字段冗余存储发帖时的用户头像，后端返回头像URL，前端创建通用头像组件处理显示和占位符逻辑。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Vue3 Composition API, TypeScript, uni-app

---

## 前置检查

**Before starting:** 确认数据库已连接且 Alembic 可用

```bash
cd backend
python3 -c "from alembic.config import main; main()" --version
```

Expected: Alembic version output

---

## Task 1: 添加 user_avatar 字段到 Post 模型

**Files:**
- Modify: `backend/app/models/post.py`

**Step 1: 添加字段到 Post 模型**

在 `Post` 类中添加 `user_avatar` 字段（在 `anonymous_name` 字段之后）:

```python
user_avatar = Column(String(255), nullable=True, comment="发帖时用户头像URL冗余")
```

**Step 2: 运行类型检查**

Run: `cd backend && python3 -m pylint app/models/post.py --disable=all --enable=E`
Expected: 无错误输出

**Step 3: 提交模型修改**

```bash
git add backend/app/models/post.py
git commit -m "feat(post): add user_avatar field to Post model

Add user_avatar column for storing user avatar URL at post creation time.
This follows the same redundancy pattern as anonymous_name.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: 创建数据库迁移文件

**Files:**
- Create: `backend/alembic/versions/<timestamp>_add_user_avatar_to_posts.py`

**Step 1: 生成迁移文件**

Run: `cd backend && alembic revision --autogenerate -m "add user_avatar to posts"`

Expected: 新迁移文件已创建在 `backend/alembic/versions/`

**Step 2: 编辑迁移文件**

打开新生成的迁移文件，确保 upgrade 函数包含：

```python
def upgrade() -> None:
    op.add_column('posts', sa.Column('user_avatar', sa.String(255), nullable=True, comment='发帖时用户头像URL冗余'))
```

**Step 3: 添加现有数据填充逻辑**

在 `upgrade()` 函数的 `op.add_column` 之后添加：

```python
    # 为现有帖子填充头像
    from sqlalchemy import text
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE posts p
        LEFT JOIN users u ON p.user_id = u.id
        SET p.user_avatar = u.avatar
        WHERE p.user_avatar IS NULL
    """))
```

downgrade 函数：

```python
def downgrade() -> None:
    op.drop_column('posts', 'user_avatar')
```

**Step 4: 验证迁移文件语法**

Run: `cd backend && python3 -m alembic check`
Expected: No errors found

**Step 5: 提交迁移文件**

```bash
git add backend/alembic/versions/
git commit -m "feat(migration): add user_avatar column to posts table

- Add user_avatar column to store avatar URL
- Backfill existing posts with user avatar from users table
- Add downgrade logic for rollback

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: 执行数据库迁移

**Files:**
- Database migration execution

**Step 1: 执行迁移**

Run: `cd backend && python3 -m alembic upgrade head`

Expected: `Running upgrade -> <revision>, add user_avatar to posts`

**Step 2: 验证字段已添加**

Run: `cd backend && python3 -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('DESCRIBE posts'))
    for row in result:
        if 'user_avatar' in row:
            print('user_avatar column exists')
"`

Expected: 输出包含 `user_avatar`

**Step 3: 验证现有数据已填充**

Run: `cd backend && python3 -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM posts WHERE user_avatar IS NOT NULL'))
    count = result.scalar()
    print(f'Posts with avatar: {count}')
"`

Expected: 数量大于0或显示0（如果没有帖子）

**Step 4: 提交迁移记录**

```bash
git add .
git commit -m "chore: apply user_avatar migration to database

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: 更新 PostResponse Schema

**Files:**
- Modify: `backend/app/schemas/post.py`

**Step 1: 添加 user_avatar 字段到 PostResponse**

在 `PostResponse` 类中添加字段（在 `anonymous_name` 之后）:

```python
user_avatar: Optional[str] = None
```

**Step 2: 验证 schema 语法**

Run: `cd backend && python3 -c "from app.schemas.post import PostResponse; print('Schema OK')"`
Expected: `Schema OK`

**Step 3: 提交 schema 修改**

```bash
git add backend/app/schemas/post.py
git commit -m "feat(schema): add user_avatar to PostResponse

Add user_avatar field to PostResponse schema for API responses.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: 修改 post_service.py - create() 函数

**Files:**
- Modify: `backend/app/services/post_service.py`

**Step 1: 在 create() 函数中添加 user_avatar 参数**

在 `post = Post(...)` 创建语句中添加 `user_avatar` 字段（在 `anonymous_name` 之后）:

```python
post = Post(
    user_id=user_id,
    anonymous_name=anonymous_name,
    user_avatar=data.user_avatar if hasattr(data, 'user_avatar') and data.user_avatar else None,  # 添加此行
    content=sanitized_content,
    # ... 其他现有字段
)
```

等等，我需要重新思考。用户头像应该从 current_user 获取，而不是从请求数据。让我修正：

在 `create()` 函数签名中添加 `user_avatar` 参数：

```python
async def create(
    db: AsyncSession,
    user_id: str,
    data: PostCreate,
    *,
    anonymous_name: str,
    user_avatar: Optional[str] = None,  # 添加此参数
) -> Post:
```

然后在 `Post` 创建中使用：

```python
post = Post(
    user_id=user_id,
    anonymous_name=anonymous_name,
    user_avatar=user_avatar,  # 添加此行
    content=sanitized_content,
    # ... 其他现有字段
)
```

**Step 2: 验证语法**

Run: `cd backend && python3 -m pylint app/services/post_service.py --disable=all --enable=E --errors-only`
Expected: 无错误

**Step 3: 提交修改**

```bash
git add backend/app/services/post_service.py
git commit -m "feat(service): add user_avatar to post creation

Update create() function to accept and store user_avatar parameter.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: 修改 post_service.py - get_by_id() 函数

**Files:**
- Modify: `backend/app/services/post_service.py`

**Step 1: 在 get_by_id() 返回字典中添加 user_avatar**

在返回字典中添加字段（在 `anonymous_name` 之后）:

```python
return {
    'id': post.id,
    'user_id': post.user_id,
    'anonymous_name': post.anonymous_name,
    'user_avatar': post.user_avatar,  # 添加此行
    'content': post.content,
    # ... 其他现有字段
}
```

**Step 2: 验证语法**

Run: `cd backend && python3 -c "from app.services.post_service import get_by_id; print('Import OK')"`
Expected: `Import OK`

**Step 3: 提交修改**

```bash
git add backend/app/services/post_service.py
git commit -m "feat(service): add user_avatar to get_by_id response

Include user_avatar in post detail response dictionary.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: 修改 post API 调用 create() 时传递头像

**Files:**
- Modify: `backend/app/api/v1/post.py`

**Step 1: 在 post_create 函数中传递 user_avatar**

找到 `await create_post()` 调用，添加 `user_avatar` 参数：

```python
@router.post("")
async def post_create(
    body: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_post),
    db: AsyncSession = Depends(get_db),
):
    # 发帖使用当前用户匿名昵称
    post = await create_post(
        db,
        current_user.id,
        body,
        anonymous_name=current_user.anonymous_name,
        user_avatar=current_user.avatar  # 添加此行
    )
    # ... 其余代码
```

**Step 2: 验证 API 启动**

Run: `cd backend && python3 -c "from app.api.v1.post import router; print('Import OK')"`
Expected: `Import OK`

**Step 3: 提交修改**

```bash
git add backend/app/api/v1/post.py
git commit -m "feat(api): pass user_avatar to post creation

Pass current user's avatar when creating a new post.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: 后端单元测试 - Post 模型

**Files:**
- Create: `backend/tests/models/test_post_model.py`

**Step 1: 创建测试文件**

```python
"""Test Post model with user_avatar field"""
import pytest
from app.models.post import Post
from datetime import datetime


def test_post_creation_with_user_avatar(db_session):
    """Test creating a post with user_avatar"""
    post = Post(
        user_id="test_user_id",
        anonymous_name="Test User",
        user_avatar="https://example.com/avatar.jpg",
        content="Test content",
        status="normal",
        risk_status="approved",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(post)
    db_session.commit()

    retrieved_post = db_session.query(Post).filter_by(id=post.id).first()
    assert retrieved_post is not None
    assert retrieved_post.user_avatar == "https://example.com/avatar.jpg"


def test_post_creation_without_user_avatar(db_session):
    """Test creating a post without user_avatar (nullable)"""
    post = Post(
        user_id="test_user_id",
        anonymous_name="Test User",
        user_avatar=None,
        content="Test content",
        status="normal",
        risk_status="approved",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(post)
    db_session.commit()

    retrieved_post = db_session.query(Post).filter_by(id=post.id).first()
    assert retrieved_post is not None
    assert retrieved_post.user_avatar is None
```

**Step 2: 运行测试**

Run: `cd backend && pytest tests/models/test_post_model.py -v`

Expected: PASS

**Step 3: 提交测试**

```bash
git add backend/tests/models/test_post_model.py
git commit -m "test(post): add tests for user_avatar field in Post model

Test post creation with and without user_avatar value.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: 后端单元测试 - post_service

**Files:**
- Modify: `backend/tests/services/test_post_service.py` (如果存在) 或 Create

**Step 1: 添加 create() 函数测试**

```python
@pytest.mark.asyncio
async def test_create_post_with_user_avatar(db_session):
    """Test creating a post includes user_avatar"""
    from app.schemas.post import PostCreate
    from app.services.post_service import create

    post_data = PostCreate(content="Test post content")
    user_avatar = "https://example.com/test_avatar.jpg"

    post = await create(
        db_session,
        user_id="test_user_123",
        data=post_data,
        anonymous_name="TestUser",
        user_avatar=user_avatar
    )

    assert post.user_avatar == user_avatar
    assert post.content == "Test post content"


@pytest.mark.asyncio
async def test_get_post_detail_includes_user_avatar(db_session):
    """Test get_by_id returns user_avatar field"""
    from app.services.post_service import create, get_by_id

    # First create a post
    from app.schemas.post import PostCreate
    post_data = PostCreate(content="Test content")
    post = await create(
        db_session,
        user_id="user_123",
        data=post_data,
        anonymous_name="AnonUser",
        user_avatar="https://example.com/avatar.png"
    )

    # Then get it back
    post_dict = await get_by_id(db_session, post.id, only_approved=False)

    assert post_dict is not None
    assert 'user_avatar' in post_dict
    assert post_dict['user_avatar'] == "https://example.com/avatar.png"
```

**Step 2: 运行测试**

Run: `cd backend && pytest tests/services/test_post_service.py -v -k "user_avatar"`

Expected: PASS

**Step 3: 提交测试**

```bash
git add backend/tests/services/test_post_service.py
git commit -m "test(service): add tests for user_avatar in post_service

Test that create() and get_by_id() properly handle user_avatar field.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: 前端 - 更新 PostItem 接口

**Files:**
- Modify: `miniapp/src/api/post.ts`

**Step 1: 在 PostItem 接口中添加 user_avatar**

```typescript
export interface PostItem {
  id: string
  user_id: string
  anonymous_name: string
  user_avatar: string | null  // 添加此行
  content: string
  // ... 其他现有字段
}
```

**Step 2: 运行类型检查**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 3: 提交修改**

```bash
git add miniapp/src/api/post.ts
git commit -m "feat(api): add user_avatar to PostItem interface

Add user_avatar field to PostItem TypeScript interface.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: 前端 - 更新 FeedPost 接口

**Files:**
- Modify: `miniapp/src/api/follow.ts`

**Step 1: 在 FeedPost 接口中添加 user_avatar**

```typescript
export interface FeedPost {
  id: string
  user_id: string
  anonymous_name: string
  user_avatar: string | null  // 添加此行
  content: string
  // ... 其他现有字段
}
```

**Step 2: 运行类型检查**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 3: 提交修改**

```bash
git add miniapp/src/api/follow.ts
git commit -m "feat(api): add user_avatar to FeedPost interface

Add user_avatar field to FeedPost TypeScript interface.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: 前端 - 创建 UserAvatar 组件

**Files:**
- Create: `miniapp/src/components/UserAvatar.vue`

**Step 1: 创建 UserAvatar.vue 组件**

```vue
<script setup lang="ts">
interface Props {
  avatar: string | null | undefined
  anonymousName: string
  size?: 'small' | 'medium' | 'large'
}

withDefaults(defineProps<Props>(), {
  size: 'medium'
})
</script>

<template>
  <image
    v-if="avatar"
    :src="avatar"
    class="avatar"
    :class="size"
    mode="aspectFill"
  />
  <view v-else class="avatar-placeholder" :class="size">
    {{ anonymousName?.substring(0, 1) || '?' }}
  </view>
</template>

<style scoped>
.avatar {
  border-radius: 50%;
  background: #f0f0f0;
  flex-shrink: 0;
}

.avatar.small {
  width: 60rpx;
  height: 60rpx;
}

.avatar.medium {
  width: 80rpx;
  height: 80rpx;
}

.avatar.large {
  width: 100rpx;
  height: 100rpx;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #07c160;
  color: #fff;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.avatar-placeholder.small {
  width: 60rpx;
  height: 60rpx;
  font-size: 24rpx;
}

.avatar-placeholder.medium {
  width: 80rpx;
  height: 80rpx;
  font-size: 32rpx;
}

.avatar-placeholder.large {
  width: 100rpx;
  height: 100rpx;
  font-size: 36rpx;
}
</style>
```

**Step 2: 验证组件语法**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 3: 提交组件**

```bash
git add miniapp/src/components/UserAvatar.vue
git commit -m "feat(component): create UserAvatar component

Create reusable avatar component with:
- Support for avatar image URL
- Fallback to placeholder with first letter of anonymous_name
- Multiple size options (small/medium/large)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 13: 前端 - 修改广场列表页添加头像

**Files:**
- Modify: `miniapp/src/pages/square/index.vue`

**Step 1: 导入 UserAvatar 组件**

在 `<script setup>` 中添加导入：

```typescript
import UserAvatar from '@/components/UserAvatar.vue'
```

**Step 2: 修改模板添加头像**

找到作者名称部分，修改模板：

```vue
<view class="author-section">
  <UserAvatar
    :avatar="item.user_avatar"
    :anonymous-name="item.anonymous_name"
    size="small"
  />
  <text class="name">{{ item.anonymous_name }}</text>
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
```

**Step 3: 调整样式（如果需要）**

确保 `.author-section` 使用 flex 布局对齐：

```css
.author-section {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
}
```

**Step 4: 运行类型检查**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 5: 提交修改**

```bash
git add miniapp/src/pages/square/index.vue
git commit -m "feat(square): add user avatar to post list

Display user avatar in square post list using UserAvatar component.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 14: 前端 - 修改帖子详情页添加头像

**Files:**
- Modify: `miniapp/src/pages/post-detail/index.vue`

**Step 1: 导入 UserAvatar 组件**

在 `<script setup>` 中添加：

```typescript
import UserAvatar from '@/components/UserAvatar.vue'
```

**Step 2: 修改模板添加头像**

在帖子作者区域添加头像组件：

```vue
<view class="row">
  <view class="author-header">
    <UserAvatar
      :avatar="post.user_avatar"
      :anonymous-name="post.anonymous_name"
      size="medium"
    />
    <view class="author-info">
      <text class="name">{{ post.anonymous_name }}</text>
      <text class="time">{{ timeStr }}</text>
    </view>
  </view>
</view>
```

**Step 3: 更新样式**

添加或修改样式：

```css
.author-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.name {
  font-weight: 600;
  font-size: 30rpx;
}

.time {
  font-size: 24rpx;
  color: #999;
}
```

**Step 4: 运行类型检查**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 5: 提交修改**

```bash
git add miniapp/src/pages/post-detail/index.vue
git commit -m "feat(post-detail): add user avatar to post detail

Display user avatar in post detail page using UserAvatar component.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 15: 前端 - 修改我的关注/点赞页添加头像

**Files:**
- Modify: `miniapp/src/pages/feed/index.vue`

**Step 1: 导入 UserAvatar 组件**

在 `<script setup>` 中添加：

```typescript
import UserAvatar from '@/components/UserAvatar.vue'
```

**Step 2: 修改"我的点赞"tab模板添加头像**

在帖子列表卡片中添加头像：

```vue
<view v-for="item in posts" :key="item.id" class="card" @click="goDetail(item.id)">
  <view class="row">
    <view class="author-section">
      <UserAvatar
        :avatar="item.user_avatar"
        :anonymous-name="item.anonymous_name"
        size="small"
      />
      <text class="name">{{ item.anonymous_name }}</text>
    </view>
    <text class="time">{{ formatTime(item.created_at) }}</text>
  </view>
  <!-- ... 其余内容保持不变 -->
</view>
```

**Step 3: 调整样式**

确保 `.author-section` 样式正确：

```css
.author-section {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
}
```

**Step 4: 运行类型检查**

Run: `cd miniapp && npm run type-check`

Expected: 无类型错误

**Step 5: 提交修改**

```bash
git add miniapp/src/pages/feed/index.vue
git commit -m "feat(feed): add user avatar to my likes tab

Display user avatar in 'my likes' post list using UserAvatar component.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 16: 前端组件测试

**Files:**
- Create: `miniapp/tests/components/UserAvatar.test.ts`

**Step 1: 创建组件测试**

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UserAvatar from '@/components/UserAvatar.vue'

describe('UserAvatar', () => {
  it('renders avatar image when avatar prop is provided', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: 'https://example.com/avatar.jpg',
        anonymousName: 'TestUser'
      }
    })

    const image = wrapper.find('image')
    expect(image.exists()).toBe(true)
    expect(image.attributes('src')).toBe('https://example.com/avatar.jpg')
  })

  it('renders placeholder when avatar is null', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: 'TestUser'
      }
    })

    const placeholder = wrapper.find('.avatar-placeholder')
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.text()).toBe('T')
  })

  it('renders question mark when anonymous_name is empty', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: ''
      }
    })

    const placeholder = wrapper.find('.avatar-placeholder')
    expect(placeholder.text()).toBe('?')
  })

  it('applies correct size class', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: 'Test',
        size: 'small'
      }
    })

    expect(wrapper.find('.small').exists()).toBe(true)
  })
})
```

**Step 2: 运行测试**

Run: `cd miniapp && npm run test -- UserAvatar.test.ts`

Expected: PASS

**Step 3: 提交测试**

```bash
git add miniapp/tests/components/UserAvatar.test.ts
git commit -m "test(component): add tests for UserAvatar component

Test avatar image rendering, placeholder fallback, and size classes.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 17: 集成测试 - 后端 API

**Files:**
- Modify: `backend/tests/integration/test_post_api.py` (如果存在)

**Step 1: 添加 API 响应测试**

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_list_includes_user_avatar(async_client):
    """Test that post list API returns user_avatar field"""
    # Create a test user and post first
    # ... setup code ...

    response = await async_client.get("/api/v1/posts?sort=latest&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    posts = data['data']

    if len(posts) > 0:
        # Check first post has user_avatar field
        assert 'user_avatar' in posts[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_detail_includes_user_avatar(async_client):
    """Test that post detail API returns user_avatar field"""
    # Create a test post first
    # ... setup code ...

    response = await async_client.get(f"/api/v1/posts/{post_id}")

    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    post = data['data']
    assert 'user_avatar' in post
```

**Step 2: 运行集成测试**

Run: `cd backend && pytest tests/integration/test_post_api.py -v -k "user_avatar"`

Expected: PASS

**Step 3: 提交测试**

```bash
git add backend/tests/integration/test_post_api.py
git commit -m "test(integration): add user_avatar tests to post API

Verify that post list and detail endpoints return user_avatar field.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 18: 端到端测试

**Files:**
- Manual testing

**Step 1: 启动后端服务**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 2: 启动前端服务**

```bash
cd miniapp
npm run dev
```

**Step 3: 手动测试清单**

- [ ] 创建新帖子，验证头像正确存储和显示
- [ ] 查看广场列表（热门），验证头像显示
- [ ] 查看广场列表（最新），验证头像显示
- [ ] 点击帖子查看详情，验证头像显示
- [ ] 查看"我的点赞"列表，验证头像显示
- [ ] 测试无头像用户，验证占位符正确显示
- [ ] 测试头像加载失败情况，验证降级处理

**Step 4: 提交文档**

```bash
git add .
git commit -m "test(e2e): complete manual testing checklist

- Verified avatar display in square list (hot/latest)
- Verified avatar display in post detail
- Verified avatar display in my likes feed
- Verified placeholder fallback for users without avatar
- Verified error handling for failed image loads

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 19: 更新 API 文档（可选）

**Files:**
- Modify: `docs/api.md` (如果存在) 或创建

**Step 1: 更新 API 文档**

在帖子相关 API 文档中添加 `user_avatar` 字段说明：

```markdown
### PostResponse Schema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Post unique identifier |
| user_id | string | Author user ID |
| anonymous_name | string | Author anonymous display name |
| user_avatar | string \| null | Author avatar URL at post creation time |
| content | string | Post content |
| ... | ... | ... |
```

**Step 2: 提交文档**

```bash
git add docs/api.md
git commit -m "docs(api): document user_avatar field in PostResponse

Add user_avatar field to API documentation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 20: 最终验证和清理

**Files:**
- All modified files

**Step 1: 运行所有后端测试**

```bash
cd backend
pytest -v
```

Expected: 所有测试通过

**Step 2: 运行所有前端测试**

```bash
cd miniapp
npm run test
```

Expected: 所有测试通过

**Step 3: 代码质量检查**

```bash
# 后端 lint
cd backend && python3 -m pylint app/models/post.py app/schemas/post.py app/services/post_service.py

# 前端 lint
cd miniapp && npm run lint
```

Expected: 无严重错误

**Step 4: 构建检查**

```bash
cd miniapp
npm run build
```

Expected: 构建成功

**Step 5: 最终提交**

```bash
git add .
git commit -m "chore: final cleanup and verification for user avatar feature

- All tests passing
- Code quality checks passing
- Build successful
- Ready for merge

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 实施完成检查清单

- [ ] 数据库迁移已执行
- [ ] 后端模型、schema、service 已更新
- [ ] 后端单元测试通过
- [ ] 后端集成测试通过
- [ ] 前端 TypeScript 接口已更新
- [ ] UserAvatar 组件已创建
- [ ] 广场列表页已添加头像
- [ ] 帖子详情页已添加头像
- [ ] 我的关注/点赞页已添加头像
- [ ] 前端组件测试通过
- [ ] 手动端到端测试完成
- [ ] API 文档已更新（可选）
- [ ] 代码质量检查通过
- [ ] 构建成功

---

## 回滚计划

如果需要回滚此功能：

```bash
# 1. 回滚数据库迁移
cd backend
alembic downgrade -1

# 2. 回滚代码更改
git revert <commit-range>

# 3. 验证回滚
pytest
npm run test
```

---

## 相关文档

- 设计文档: `docs/plans/2026-02-23-user-avatar-display-design.md`
- 技术方案: `docs/技术方案_v1.0.md`
- 迭代规划: `docs/迭代规划_Sprint与任务.md`

---

**计划完成日期**: 2026-02-23
**预计工时**: 4-6 小时
**优先级**: 中等
**风险等级**: 低（仅新增字段，不影响现有逻辑）
