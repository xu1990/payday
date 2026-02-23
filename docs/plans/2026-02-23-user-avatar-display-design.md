# 用户头像显示功能设计文档

**日期**: 2026-02-23
**作者**: Claude
**状态**: 已批准

## 1. 概述

### 1.1 目标
在小程序端的广场列表页、帖子详情页、我的关注/点赞页中添加用户头像显示，提升用户体验和社交互动性。

### 1.2 范围
- **广场列表页** (`square/index.vue`) - 显示热门/最新帖子
- **帖子详情页** (`post-detail/index.vue`) - 查看单个帖子和评论
- **我的关注/点赞页** (`feed/index.vue`) - 显示我关注的人和我点赞的帖子

## 2. 技术方案

### 2.1 方案选择
**方案A：冗余存储 + 最小查询**（已选定）

**原理**：在 `Post` 表中新增 `user_avatar` 字段，发帖时从 User 表复制头像 URL

**优点**：
- 查询性能最佳，无需 join 用户表
- 帖子数据独立，即使用户修改头像也不影响历史帖子显示
- 实现简单，改动最小
- 与现有 `anonymous_name` 冗余存储设计理念一致

**缺点**：
- 需要数据库迁移
- 数据冗余
- 用户修改头像后，历史帖子仍显示旧头像（合理行为）

## 3. 数据库层设计

### 3.1 模型修改
**文件**: `backend/app/models/post.py`

在 `Post` 类中新增字段：
```python
user_avatar = Column(String(255), nullable=True, comment="发帖时用户头像URL冗余")
```

### 3.2 数据库迁移
创建 Alembic 迁移文件：
- 在 `posts` 表添加 `user_avatar` 字段
- 为现有数据填充头像（从 users 表 join 获取）

迁移脚本：
```python
def upgrade():
    op.add_column('posts', sa.Column('user_avatar', sa.String(255), nullable=True))

    # 为现有帖子填充头像
    from alembic import op
    op.execute("""
        UPDATE posts p
        LEFT JOIN users u ON p.user_id = u.id
        SET p.user_avatar = u.avatar
        WHERE p.user_avatar IS NULL
    """)
```

### 3.3 服务层修改
**文件**: `backend/app/services/post_service.py`

#### 3.3.1 修改 `create()` 函数
发帖时从当前用户获取头像：
```python
post = Post(
    # ... 现有字段
    user_avatar=current_user.avatar,  # 新增
)
```

#### 3.3.2 修改 `get_by_id()` 函数
在返回字典中添加 `user_avatar`：
```python
return {
    # ... 现有字段
    'user_avatar': post.user_avatar,
}
```

## 4. 后端API层设计

### 4.1 Schema 修改
**文件**: `backend/app/schemas/post.py`

```python
class PostResponse(BaseModel):
    # ... 现有字段
    user_avatar: Optional[str] = None

    class Config:
        from_attributes = True
```

### 4.2 API端点验证
确保以下API返回包含 `user_avatar`：
- `/api/v1/posts` (列表) - 自动通过 `PostResponse.model_validate()` 包含
- `/api/v1/posts/{post_id}` (详情) - 在 `get_by_id()` 返回字典中添加
- `/api/v1/posts/search` (搜索) - 自动包含

## 5. 前端API层设计

### 5.1 更新 PostItem 接口
**文件**: `miniapp/src/api/post.ts`

```typescript
export interface PostItem {
  // ... 现有字段
  user_avatar: string | null
}
```

### 5.2 更新 FeedPost 接口
**文件**: `miniapp/src/api/follow.ts`

```typescript
export interface FeedPost {
  // ... 现有字段
  user_avatar: string | null
}
```

## 6. 前端UI层设计

### 6.1 创建头像组件
**文件**: `miniapp/src/components/UserAvatar.vue`

```vue
<script setup lang="ts">
defineProps<{
  avatar: string | null | undefined
  anonymousName: string
  size?: 'small' | 'medium' | 'large'
}>()
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

### 6.2 修改广场列表页
**文件**: `miniapp/src/pages/square/index.vue`

在作者区域添加头像：
```vue
<template>
  <view class="author-section">
    <UserAvatar
      :avatar="item.user_avatar"
      :anonymous-name="item.anonymous_name"
      size="small"
    />
    <text class="name">{{ item.anonymous_name }}</text>
    <FollowButton ... />
  </view>
</template>
```

### 6.3 修改帖子详情页
**文件**: `miniapp/src/pages/post-detail/index.vue`

在帖子作者区域添加头像：
```vue
<template>
  <view class="author-row">
    <UserAvatar
      :avatar="post.user_avatar"
      :anonymous-name="post.anonymous_name"
      size="medium"
    />
    <text class="name">{{ post.anonymous_name }}</text>
    <FollowButton ... />
  </view>
</template>
```

### 6.4 修改我的关注/点赞页
**文件**: `miniapp/src/pages/feed/index.vue`

在"我的点赞" tab 的帖子列表中添加头像（用户列表已有头像，无需修改）：
```vue
<template>
  <view class="card" @click="goDetail(item.id)">
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
    <!-- ... 其他内容 -->
  </view>
</template>
```

## 7. 兼容性与边界情况

### 7.1 向后兼容性
- 后端：`user_avatar` 为可选字段（nullable），旧数据为 NULL
- 前端：头像组件处理 `null/undefined` 情况，显示占位符（首字母）

### 7.2 用户修改头像后的行为
- **新帖子**：使用用户当前头像
- **历史帖子**：保持发帖时的头像（这是合理行为，与 `anonymous_name` 一致）
- **用户主页**：显示最新头像

### 7.3 无头像用户
- 显示占位符：圆形背景 + 匿名昵称首字母
- 背景色：绿色 (#07c160)
- 样式与现有设计保持一致

## 8. 测试计划

### 8.1 后端测试
- [ ] 发帖时验证头像正确存储到 `posts.user_avatar`
- [ ] 验证帖子列表API返回 `user_avatar`
- [ ] 验证帖子详情API返回 `user_avatar`
- [ ] 验证搜索API返回 `user_avatar`

### 8.2 前端测试
- [ ] 验证广场列表页正确显示头像
- [ ] 验证帖子详情页正确显示头像
- [ ] 验证我的关注/点赞页正确显示头像
- [ ] 验证无头像用户显示占位符
- [ ] 验证头像组件不同 size 样式正确

### 8.3 数据迁移测试
- [ ] 验证迁移脚本正确添加字段
- [ ] 验证现有帖子数据正确填充头像
- [ ] 验证 NULL 值处理正确

## 9. 实施清单

### 后端
- [ ] 修改 `backend/app/models/post.py` - 添加 `user_avatar` 字段
- [ ] 修改 `backend/app/schemas/post.py` - 更新 `PostResponse`
- [ ] 修改 `backend/app/services/post_service.py` - 更新 `create()` 和 `get_by_id()`
- [ ] 创建 Alembic 迁移文件
- [ ] 运行迁移：`alembic upgrade head`
- [ ] 运行后端测试：`pytest`

### 前端
- [ ] 创建 `miniapp/src/components/UserAvatar.vue`
- [ ] 修改 `miniapp/src/api/post.ts` - 更新 `PostItem`
- [ ] 修改 `miniapp/src/api/follow.ts` - 更新 `FeedPost`
- [ ] 修改 `miniapp/src/pages/square/index.vue` - 添加头像
- [ ] 修改 `miniapp/src/pages/post-detail/index.vue` - 添加头像
- [ ] 修改 `miniapp/src/pages/feed/index.vue` - 添加头像
- [ ] 运行前端测试：`npm run test:miniapp`

## 10. 风险与注意事项

1. **数据库迁移**：确保在低峰期执行，备份数据
2. **性能影响**：新增字段对查询性能影响极小（仅一个字符串字段）
3. **存储成本**：每个帖子增加约 100 字节（假设头像URL平均长度）
4. **缓存失效**：帖子缓存需要刷新以包含新字段

## 11. 后续优化

1. **头像压缩**：如果需要，可以添加头像 CDN 优化
2. **头像默认值**：为新用户生成随机头像（可选）
3. **批量查询优化**：如果未来需要实时头像，可考虑批量查询用户表
