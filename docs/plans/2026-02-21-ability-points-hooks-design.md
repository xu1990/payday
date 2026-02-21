# 能力值钩子系统设计方案

**文档版本**: v1.0
**创建日期**: 2026-02-21
**设计者**: Technical Architect
**对应 PRD**: PRD_v1.2_detail.md
**状态**: ✅ 已批准

---

## 一、概述

### 1.1 设计目标

为薪日 PayDay v1.2 设计一个**完整的能力值钩子系统**，作为整个「成长体系」的核心基础设施：

- 支持 18 种能力值事件（同步 + 异步）
- 每日行为限制（发帖 10 次/天、评论 20 次/天等）
- 能力值增加与扣减（支持负数）
- 等级自动计算与升级/降级
- 能力值排行榜（日/周/月/总榜）
- 完整的日志记录与审计

### 1.2 核心设计决策

| 决策点 | 选择方案 | 理由 |
|--------|----------|------|
| **原子性保证** | 混合模式 | 关键操作（兑换、扣减）用事务，普通操作（点赞、评论）用异步 |
| **钩子触发方式** | 事件驱动 | 完全解耦，易于扩展和监控 |
| **事件总线** | Celery | 复用现有基础设施，持久化、支持重试、分布式 |
| **每日限制** | 混合模式 | Redis 实时检查 + 定时同步到数据库 |
| **扣减策略** | 完整扣减系统 | 支持扣到负数，等级可下降，完整奖惩体系 |

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    业务服务层                            │
│  (post_service, comment_service, reward_service, etc.)  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ 发布事件
                  ↓
┌─────────────────────────────────────────────────────────┐
│              事件总线 (Celery Tasks)                     │
│         ability_event_task.delay(event_name, data)       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ 处理事件
                  ↓
┌─────────────────────────────────────────────────────────┐
│              能力值服务 (AbilityService)                 │
│  ┌──────────────┬───────────────┬──────────────────┐  │
│  │ 钩子注册表    │ 每日限制检查   │ 扣减/增加逻辑     │  │
│  │ hooks_map    │ Redis + DB    │ 日志记录          │  │
│  └──────────────┴───────────────┴──────────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ 写入
                  ↓
┌─────────────────────────────────────────────────────────┐
│              持久化存储                                  │
│  • users.ability_points, ability_level                 │
│  • ability_points_logs                                 │
│  • daily_action_counts (DB)                            │
│  • ability:daily_limit:* (Redis)                       │
│  • leaderboard:ability_points:* (Redis ZSet)           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 事件流

```
用户行为
    ↓
业务服务处理（核心逻辑）
    ↓
发布事件到 Celery
    ↓
AbilityService 订阅并处理
    ↓
检查每日限制（Redis）
    ↓
更新能力值（DB）
    ↓
记录日志（DB）
    ↓
更新排行榜（Redis ZSet）
    ↓
返回结果
```

---

## 三、事件定义与钩子注册

### 3.1 事件类型分类

#### 同步处理事件（SYNC_EVENTS）
关键操作，使用数据库事务保证原子性：

```python
SYNC_EVENTS = [
    "reward.order.created",      # 兑换奖励 -2000 能力值
    "reward.order.cancelled",    # 取消订单 +2000 能力值
    "admin.points.deduct",       # 管理员扣减（处罚）
    "admin.points.adjust",       # 管理员调整（运营）
]
```

#### 异步处理事件（ASYNC_EVENTS）
普通操作，通过 Celery 异步处理：

```python
ASYNC_EVENTS = {
    # 社区互动
    "post.created": 20,           # 发帖 +20
    "comment.created": 5,         # 评论 +5
    "like.created": 1,            # 点赞 +1
    "like.received": 2,           # 被赞 +2
    "follow.received": 10,        # 被关注 +10

    # 内容记录
    "salary.created": 10,         # 记工资 +10
    "expense.created": 5,         # 记支出 +5
    "salary.delayed": 5,          # 延迟吐槽 +5

    # 打卡与目标
    "checkin.overtime": 5,        # 加班打卡 +5
    "checkin.payday": 10,         # 发薪打卡 +10
    "checkin.savings": 20,        # 存款打卡 +20
    "savings.goal.achieved": 50,  # 完成存款目标 +50

    # 其他
    "user.daily_login": 1,        # 每日登录 +1
    "user.invite": 100,           # 邀请好友 +100
}
```

#### 扣减事件（DEDUCT_EVENTS）
反向操作，扣减能力值：

```python
DEDUCT_EVENTS = [
    ("post.deleted", -20),        # 删除帖子 -20
    ("comment.deleted", -5),      # 删除评论 -5
    ("spam.penalized", -100),     # 刷量处罚 -100
]
```

### 3.2 每日限制配置

```python
DAILY_LIMITS = {
    "post.created": 10,           # 发帖 10 次/天
    "comment.created": 20,        # 评论 20 次/天
    "like.created": 50,           # 点赞 50 次/天
    "checkin.overtime": 3,        # 打卡 3 次/天
    "user.invite": 10,            # 邀请 10 人
}
```

### 3.3 钩子注册机制

```python
class AbilityService:
    def __init__(self):
        self.hooks_map = defaultdict(list)
        self._register_default_hooks()

    def _register_default_hooks(self):
        # 注册同步事件处理
        for event in SYNC_EVENTS:
            self.register_hook(event, self._handle_sync_event)

        # 注册异步事件处理
        for event, points in ASYNC_EVENTS.items():
            self.register_hook(event,
                lambda data, p=points: self._handle_add_points(data, p))

        # 注册扣减事件
        for event, points in DEDUCT_EVENTS:
            self.register_hook(event,
                lambda data, p=points: self._handle_deduct_points(data, p))

    def register_hook(self, event_name: str, handler: Callable):
        """注册事件处理钩子"""
        self.hooks_map[event_name].append(handler)
```

---

## 四、核心服务实现

### 4.1 AbilityService 核心方法

```python
class AbilityService:
    """能力值服务 - 完整实现"""

    async def add_points(
        self,
        user_id: str,
        action_type: str,
        points: int,
        target_id: str | None = None,
        is_sync: bool = False
    ) -> AbilityPointsLog:
        """
        增加能力值

        Args:
            user_id: 用户ID
            action_type: 行为类型 (如 'post.created')
            points: 变化值（正数）
            target_id: 关联内容ID
            is_sync: 是否同步处理（数据库事务）
        """
        # 1. 检查每日限制
        if action_type in DAILY_LIMITS:
            await self._check_daily_limit(user_id, action_type)

        # 2. 同步处理（关键操作）
        if is_sync:
            return await self._add_points_sync(
                user_id, action_type, points, target_id
            )

        # 3. 异步处理（普通操作）- 通过 Celery
        return await ability_event_task.delay(
            user_id, action_type, points, target_id
        )

    async def deduct_points(
        self,
        user_id: str,
        action_type: str,
        points: int,
        target_id: str | None = None,
        reason: str | None = None
    ) -> AbilityPointsLog:
        """
        扣减能力值（支持负数）

        Args:
            points: 扣减值（正数，内部转为负数）
        """
        async with get_db().begin():  # 事务保证
            # 1. 计算新能力值（可以为负）
            user = await self._get_user(user_id)
            new_points = user.ability_points - points

            # 2. 更新用户能力值
            user.ability_points = new_points

            # 3. 重新计算等级（可能下降）
            new_level = self._calculate_level(new_points)
            if new_level != user.ability_level:
                user.ability_level = new_level
                user.ability_level_updated_at = datetime.now()

            # 4. 写入日志
            log = AbilityPointsLog(
                user_id=user_id,
                points_change=-points,  # 负数
                action_type=action_type,
                target_id=target_id,
                description=reason or f"扣减能力值: {action_type}"
            )
            db.add(log)

            return log
```

### 4.2 每日限制检查（Redis + DB 混合）

```python
async def _check_daily_limit(
    self,
    user_id: str,
    action_type: str
):
    """检查每日限制（Redis 实时）"""
    limit = DAILY_LIMITS.get(action_type)
    if not limit:
        return

    # Redis key: ability:daily_limit:{user_id}:{action_type}:{YYYY-MM-DD}
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"ability:daily_limit:{user_id}:{action_type}:{today}"

    # 原子递增
    current_count = await redis.incr(key)

    # 设置过期时间（到今日 23:59:59）
    seconds_until_midnight = (86400 - int(time.time()) % 86400)
    await redis.expire(key, seconds_until_midnight)

    # 检查是否超限
    if current_count > limit:
        # 回滚计数（因为本次操作失败）
        await redis.decr(key)
        raise DailyLimitExceeded(
            f"今日{action_type}次数已达上限({limit}次)"
        )
```

### 4.3 等级计算逻辑

```python
def _calculate_level(self, points: int) -> int:
    """
    根据能力值计算等级（支持下降）

    等级划分：
    1: 职场新人     0-99
    2: 打工小白   100-499
    3: 熟练工     500-999
    4: 职场老手 1000-2999
    5: 打工皇帝    3000+
    """
    if points < 0:
        return 1  # 负数时显示为最低等级
    elif points < 100:
        return 1
    elif points < 500:
        return 2
    elif points < 1000:
        return 3
    elif points < 3000:
        return 4
    else:
        return 5

def get_level_name(self, level: int) -> str:
    LEVEL_NAMES = {
        1: "职场新人",
        2: "打工小白",
        3: "熟练工",
        4: "职场老手",
        5: "打工皇帝"
    }
    return LEVEL_NAMES.get(level, "职场新人")
```

### 4.4 Celery 事件处理任务

```python
@celery_app.task(bind=True, max_retries=3)
def ability_event_task(
    self,
    user_id: str,
    action_type: str,
    points: int,
    target_id: str | None
):
    """异步处理能力值事件"""
    try:
        ability_service = AbilityService()
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            ability_service._add_points_async(
                user_id, action_type, points, target_id
            )
        )
    except Exception as e:
        # 重试机制
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        # 最终失败记录日志
        logger.error(f"能力值事件处理失败: {action_type}, user: {user_id}, error: {e}")
```

---

## 五、数据模型与存储

### 5.1 数据库表设计

#### ability_points_logs 表（能力值日志）

```sql
CREATE TABLE ability_points_logs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL COMMENT '用户ID',
  points_change INT NOT NULL COMMENT '能力值变化（正负）',
  action_type VARCHAR(50) NOT NULL COMMENT '行为类型',
  target_id VARCHAR(36) COMMENT '关联内容ID',
  description VARCHAR(200) COMMENT '描述',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_created_at (created_at),
  INDEX idx_action_type (action_type),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能力值日志表';
```

#### daily_action_counts 表（每日行为统计）

```sql
CREATE TABLE daily_action_counts (
  user_id VARCHAR(36) NOT NULL,
  action_date DATE NOT NULL COMMENT '行为日期',
  action_type VARCHAR(50) NOT NULL COMMENT '行为类型',
  count INT DEFAULT 0 COMMENT '次数',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, action_date, action_type),
  INDEX idx_action_date (action_date),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日行为统计表';
```

#### users 表扩展字段（已在 Sprint 4.1 定义）

```sql
ALTER TABLE users
ADD COLUMN ability_points INT DEFAULT 0 COMMENT '能力值',
ADD COLUMN ability_level INT DEFAULT 1 COMMENT '能力等级',
ADD COLUMN ability_level_updated_at TIMESTAMP NULL COMMENT '等级更新时间';
```

### 5.2 Redis 缓存结构

```
# 每日限制计数器
ability:daily_limit:{user_id}:{action_type}:{YYYY-MM-DD}
  - TTL: 到今日 23:59:59
  - 示例: ability:daily_limit:user123:post.created:2026-02-21 = 3

# 用户能力值缓存
user:ability:{user_id}
  - TTL: 1 小时
  - 内容: {"points": 1280, "level": 3, "level_name": "熟练工"}

# 能力值排行榜
leaderboard:ability_points:total      # 总榜
leaderboard:ability_points:daily       # 日榜
leaderboard:ability_points:weekly      # 周榜
leaderboard:ability_points:monthly     # 月榜
  - 类型: Sorted Set (ZSet)
  - Score: 能力值变化值
  - Member: user_id
```

### 5.3 定时同步任务

```python
@celery_app.task
def sync_daily_limits_to_db():
    """每小时同步 Redis 计数器到数据库"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 扫描所有 Redis key
    for key in redis.scan(f"ability:daily_limit:*:{today}"):
        # 解析 key 获取 user_id, action_type
        _, _, user_id, action_type, _ = key.split(":")
        count = int(redis.get(key))

        # 更新到数据库
        await db.execute(
            insert(daily_action_counts)
            .values(
                user_id=user_id,
                action_date=today,
                action_type=action_type,
                count=count
            )
            .on_duplicate_key_update(count=count)
        )
```

---

## 六、业务流程示例

### 6.1 场景 1：用户发布帖子（异步增加能力值）

```python
# 1. 用户发帖 - post_service.py
async def create_post(user_id: str, content: str):
    async with get_db().begin():
        post = Post(user_id=user_id, content=content)
        db.add(post)
        db.flush()  # 获取 post.id

        # 发布事件（Celery 异步）
        await event_bus.emit("post.created", {
            "user_id": user_id,
            "post_id": post.id,
            "content": content[:50]  # 用于日志描述
        })

        return post

# 2. Celery 任务处理
@celery_app.task
def process_post_created_event(event_data: dict):
    ability_service = AbilityService()
    loop = asyncio.get_event_loop()

    # 异步增加能力值
    log = loop.run_until_complete(
        ability_service.add_points(
            user_id=event_data["user_id"],
            action_type="post.created",
            points=20,
            target_id=event_data["post_id"]
        )
    )

    return log.id

# 3. 能力值服务处理
async def add_points(...):
    # 检查每日限制（Redis）
    await self._check_daily_limit(user_id, "post.created")  # 10次/天

    # 增加能力值
    user = await self._get_user(user_id)
    user.ability_points += 20

    # 计算新等级
    new_level = self._calculate_level(user.ability_points)
    if new_level > user.ability_level:
        user.ability_level = new_level
        user.ability_level_updated_at = datetime.now()

    # 写入日志
    log = AbilityPointsLog(
        user_id=user_id,
        points_change=20,
        action_type="post.created",
        target_id=post_id,
        description=f"发布帖子: {content[:50]}"
    )
    db.add(log)

    # 更新排行榜
    await self._update_leaderboard(user_id, 20, "total")

    return log
```

### 6.2 场景 2：用户兑换奖励（同步扣减，事务保证）

```python
# 1. 用户兑换 - reward_service.py
async def create_order(
    user_id: str,
    reward_item_id: str,
    shipping_address: str
):
    ability_service = AbilityService()

    async with get_db().begin():  # 事务开始
        # 1. 检查能力值
        user = await self._get_user(user_id)
        reward_item = await self._get_reward_item(reward_item_id)

        if user.ability_points < reward_item.points_cost:
            raise InsufficientAbilityPoints(
                f"能力值不足，需要 {reward_item.points_cost}，当前 {user.ability_points}"
            )

        # 2. 同步扣减能力值（事务内）
        await ability_service.deduct_points(
            user_id=user_id,
            action_type="reward.order.created",
            points=reward_item.points_cost,
            target_id=reward_item.id,
            reason=f"兑换: {reward_item.name}",
            is_sync=True  # 同步处理
        )

        # 3. 检查并扣减库存（原子操作）
        success = await self._decrement_stock(reward_item_id)
        if not success:
            raise OutOfStock("库存不足")

        # 4. 创建订单
        order = RewardOrder(
            user_id=user_id,
            reward_item_id=reward_item_id,
            points_used=reward_item.points_cost,
            status="pending",
            shipping_address=shipping_address
        )
        db.add(order)

        # 5. 发布事件（通知等）
        await event_bus.emit("reward.order.created", {
            "user_id": user_id,
            "order_id": order.id,
            "points_used": reward_item.points_cost
        })

        return order
    # 事务提交：要么全部成功，要么全部回滚
```

### 6.3 场景 3：删除违规帖子（扣减能力值）

```python
# 1. 管理员删除帖子 - admin/post_service.py
async def delete_post_by_admin(post_id: str, reason: str):
    ability_service = AbilityService()

    async with get_db().begin():
        # 1. 获取帖子
        post = await db.get(Post, post_id)
        if not post:
            raise NotFoundException("帖子不存在")

        # 2. 删除帖子
        await db.delete(post)

        # 3. 查找发帖时的能力值日志
        original_log = await db.execute(
            select(AbilityPointsLog)
            .where(
                AbilityPointsLog.target_id == post_id,
                AbilityPointsLog.action_type == "post.created"
            )
        ).scalar_one_or_none()

        # 4. 如果找到了原始日志，扣减相应的能力值
        if original_log:
            await ability_service.deduct_points(
                user_id=post.user_id,
                action_type="post.deleted",
                points=abs(original_log.points_change),  # 扣减原始获得的能力值
                target_id=post_id,
                reason=f"删除帖子（违规）: {reason}",
                is_sync=True
            )

        # 5. 发送通知
        await notification_service.send(
            user_id=post.user_id,
            type="post_deleted",
            content=f"您的帖子因违反社区规则被删除，原因：{reason}。已扣除相应能力值。"
        )

        return {"success": True}
```

### 6.4 场景 4：用户取消订单（返还能力值）

```python
# 1. 取消订单 - reward_service.py
async def cancel_order(user_id: str, order_id: str):
    ability_service = AbilityService()

    async with get_db().begin():
        # 1. 获取订单
        order = await db.get(RewardOrder, order_id)
        if not order or order.user_id != user_id:
            raise NotFoundException("订单不存在")

        if order.status not in ["pending", "processing"]:
            raise BusinessException("订单状态不允许取消")

        # 2. 返还能力值（同步）
        await ability_service.add_points(
            user_id=user_id,
            action_type="reward.order.cancelled",
            points=order.points_used,  # 返还消耗的能力值
            target_id=order_id,
            reason="取消订单返还",
            is_sync=True
        )

        # 3. 恢复库存
        await self._increment_stock(order.reward_item_id)

        # 4. 更新订单状态
        order.status = "cancelled"

        return order
```

---

## 七、排行榜实现

### 7.1 LeaderboardService

```python
class LeaderboardService:
    """能力值排行榜服务"""

    LEADERBOARDS = {
        "total": "leaderboard:ability_points:total",
        "daily": "leaderboard:ability_points:daily",
        "weekly": "leaderboard:ability_points:weekly",
        "monthly": "leaderboard:ability_points:monthly"
    }

    async def update_leaderboard(
        self,
        user_id: str,
        points_delta: int,
        leaderboard_type: str = "total"
    ):
        """更新排行榜"""
        key = self.LEADERBOARDS[leaderboard_type]

        # ZINCRBY：原子操作
        await redis.zincrby(key, points_delta, user_id)

        # 设置过期时间
        if leaderboard_type == "daily":
            await redis.expire(key, 86400)  # 24小时
        elif leaderboard_type == "weekly":
            await redis.expire(key, 604800)  # 7天
        elif leaderboard_type == "monthly":
            await redis.expire(key, 2592000)  # 30天
        # total 榜单不过期

    async def get_leaderboard(
        self,
        leaderboard_type: str = "total",
        limit: int = 100,
        offset: int = 0
    ) -> List[LeaderboardEntry]:
        """获取排行榜"""
        key = self.LEADERBOARDS[leaderboard_type]

        # ZREVRANGE：倒序获取（分数从高到低）
        results = await redis.zrevrange(
            key,
            offset,
            offset + limit - 1,
            withscores=True
        )

        # 批量获取用户信息
        user_ids = [user_id for user_id, _ in results]
        users = await self._batch_get_users(user_ids)

        # 组装结果
        entries = []
        for rank, (user_id, score) in enumerate(results, start=offset + 1):
            user = users.get(user_id)
            entries.append(LeaderboardEntry(
                rank=rank,
                userId=user_id,
                anonymousName=user.anonymous_name if user else "未知用户",
                avatar=user.avatar if user else None,
                abilityPoints=int(score),
                level=user.ability_level if user else 1
            ))

        return entries

    async def get_user_rank(
        self,
        user_id: str,
        leaderboard_type: str = "total"
    ) -> int:
        """获取用户排名"""
        key = self.LEADERBOARDS[leaderboard_type]

        # ZREVRANK：获取排名（从 0 开始）
        rank = await redis.zrevrank(key, user_id)

        return rank + 1 if rank is not None else None  # 转为从 1 开始
```

### 7.2 定时刷新任务

```python
@celery_app.task
def refresh_leaderboards():
    """刷新排行榜（每日、每周、每月重置）"""
    today = datetime.now().date()

    # 日榜：每日 00:00 重置
    if datetime.now().hour == 0:
        await redis.delete("leaderboard:ability_points:daily")

    # 周榜：每周一 00:00 重置
    if today.weekday() == 0 and datetime.now().hour == 0:
        await redis.delete("leaderboard:ability_points:weekly")

    # 月榜：每月 1 日 00:00 重置
    if today.day == 1 and datetime.now().hour == 0:
        await redis.delete("leaderboard:ability_points:monthly")

    # 总榜：不重置，累积记录
```

---

## 八、API 接口定义

### 8.1 获取能力值统计

```typescript
GET /api/v1/user/ability-points

Response: {
  "currentPoints": 1280,           // 当前能力值
  "level": 3,                      // 等级
  "levelName": "熟练工",           // 等级名称
  "nextLevelPoints": 3000,         // 下一等级所需能力值
  "progress": 42.67,               // 进度百分比
  "todayGained": 35,               // 今日获得能力值
  "todayActions": [                // 今日行为列表
    {
      "actionType": "post.created",
      "points": 20,
      "completed": true,
      "currentCount": 1,
      "maxCount": 10
    },
    {
      "actionType": "daily_login",
      "points": 1,
      "completed": true,
      "currentCount": 1,
      "maxCount": 1
    }
  ]
}
```

### 8.2 获取能力值日志

```typescript
GET /api/v1/user/ability-points/logs?limit=20&offset=0

Response: {
  "total": 156,
  "logs": [
    {
      "id": "log_123",
      "pointsChange": 20,
      "actionType": "post.created",
      "targetId": "post_456",
      "description": "发布帖子: 我的第一笔工资",
      "createdAt": "2026-02-21T10:30:00Z"
    },
    {
      "id": "log_124",
      "pointsChange": 5,
      "actionType": "comment.created",
      "targetId": "comment_789",
      "description": "发表评论",
      "createdAt": "2026-02-21T10:35:00Z"
    },
    {
      "id": "log_125",
      "pointsChange": -20,
      "actionType": "post.deleted",
      "targetId": "post_456",
      "description": "删除帖子（违规）: 含广告内容",
      "createdAt": "2026-02-21T11:00:00Z"
    }
  ]
}
```

### 8.3 能力值排行榜

```typescript
GET /api/v1/leaderboard/ability-points?type=total&limit=100

Query Parameters:
  - type: "total" | "daily" | "weekly" | "monthly"
  - limit: 返回数量（默认 100）

Response: {
  "leaderboardType": "total",
  "updatedAt": "2026-02-21T12:00:00Z",
  "entries": [
    {
      "rank": 1,
      "userId": "user_123",
      "anonymousName": "匿名用户_8a3f",
      "avatar": "https://...",
      "abilityPoints": 15800,
      "level": 5
    },
    {
      "rank": 2,
      "userId": "user_456",
      "anonymousName": "匿名用户_b2d1",
      "avatar": "https://...",
      "abilityPoints": 12450,
      "level": 5
    }
  ],
  "myRank": {
    "rank": 156,
    "userId": "user_789",
    "anonymousName": "匿名用户_c4e8",
    "abilityPoints": 1280,
    "level": 3
  }
}
```

---

## 九、集成指南

### 9.1 如何让现有模块支持能力值

#### 步骤 1：在业务服务中发布事件

```python
# 示例：让现有的 comment_service 支持能力值

# app/services/comment_service.py（修改前）
async def create_comment(user_id: str, post_id: str, content: str):
    comment = Comment(user_id=user_id, post_id=post_id, content=content)
    db.add(comment)
    await db.commit()
    return comment

# app/services/comment_service.py（修改后）
from app.core.event_bus import event_bus

async def create_comment(user_id: str, post_id: str, content: str):
    comment = Comment(user_id=user_id, post_id=post_id, content=content)
    db.add(comment)
    await db.commit()

    # ✅ 新增：发布评论创建事件
    await event_bus.emit("comment.created", {
        "user_id": user_id,
        "comment_id": comment.id,
        "post_id": post_id,
        "content": content[:50]
    })

    return comment
```

#### 步骤 2：在 ability_service 中注册钩子

```python
# app/services/ability_service.py（初始化时）

class AbilityService:
    def _register_default_hooks(self):
        # ... 现有钩子 ...

        # ✅ 新增：注册评论钩子
        self.register_hook(
            "comment.created",
            lambda data: self._handle_add_points(data, points=5)
        )
```

### 9.2 最小化集成清单

| 模块 | 需要修改的文件 | 修改内容 |
|------|---------------|----------|
| 帖子 | `post_service.py` | 发布 `post.created` / `post.deleted` 事件 |
| 评论 | `comment_service.py` | 发布 `comment.created` 事件 |
| 点赞 | `like_service.py` | 发布 `like.created` 事件，处理 `like.received` |
| 关注 | `follow_service.py` | 发布 `follow.created` 事件，处理 `follow.received` |
| 工资 | `salary_service.py` | 发布 `salary.created` / `salary.delayed` 事件 |
| 支出 | `expense_service.py` | 发布 `expense.created` 事件（新增） |
| 存款 | `savings_service.py` | 发布 `savings.goal.achieved` 事件（新增） |
| 打卡 | `checkin_service.py` | 发布 `checkin.*` 事件（新增） |
| 奖励 | `reward_service.py` | 发布 `reward.order.*` 事件（新增） |

---

## 十、异常处理与监控

### 10.1 异常类型

```python
# app/core/exceptions.py

class DailyLimitExceeded(BusinessException):
    """每日限制超出"""
    def __init__(self, message: str, action_type: str = None):
        super().__init__(
            message=message,
            code="DAILY_LIMIT_EXCEEDED",
            details={"action_type": action_type} if action_type else None
        )

class InsufficientAbilityPoints(BusinessException):
    """能力值不足"""
    def __init__(self, required: int, current: int):
        super().__init__(
            message=f"能力值不足，需要 {required}，当前 {current}",
            code="INSUFFICIENT_ABILITY_POINTS",
            details={"required": required, "current": current}
        )

class AbilityPointsNegative(BusinessException):
    """能力值将为负数（警告，不阻断）"""
    def __init__(self, current: int, deduct: int):
        super().__init__(
            message=f"扣减后能力值将为负数（{current - deduct}）",
            code="ABILITY_POINTS_NEGATIVE",
            details={"current": current, "deduct": deduct}
        )
```

### 10.2 监控指标

```python
# app/utils/ability_metrics.py

class AbilityMetrics:
    """能力值系统监控指标"""

    @staticmethod
    async def record_points_change(
        user_id: str,
        action_type: str,
        points: int,
        is_sync: bool
    ):
        """记录能力值变化指标"""
        await metrics.increment(
            "ability_points.change",
            tags={
                "action_type": action_type,
                "is_sync": str(is_sync),
                "is_positive": str(points > 0)
            }
        )

    @staticmethod
    async def record_daily_limit_hit(user_id: str, action_type: str):
        """记录每日限制命中"""
        await metrics.increment(
            "ability_points.daily_limit_hit",
            tags={"action_type": action_type}
        )

    @staticmethod
    async def record_level_up(user_id: str, old_level: int, new_level: int):
        """记录等级提升"""
        await metrics.increment(
            "ability_points.level_up",
            tags={
                "old_level": str(old_level),
                "new_level": str(new_level)
            }
        )

    @staticmethod
    async def record_level_down(user_id: str, old_level: int, new_level: int):
        """记录等级下降"""
        await metrics.increment(
            "ability_points.level_down",
            tags={
                "old_level": str(old_level),
                "new_level": str(new_level)
            }
        )
```

### 10.3 健康检查端点

```python
# app/api/v1/health.py

@router.get("/ability-system")
async def check_ability_system_health():
    """能力值系统健康检查"""
    health_status = {
        "status": "healthy",
        "checks": {}
    }

    # 1. Redis 连接检查
    try:
        await redis.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {e}"

    # 2. Celery 队列检查
    try:
        queue_size = await ability_event_task.queue_size()
        health_status["checks"]["celery_queue_size"] = queue_size
        if queue_size > 1000:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["celery"] = f"error: {e}"

    # 3. 负数能力值用户数
    try:
        negative_count = await db.execute(
            select(func.count(User.id))
            .where(User.ability_points < 0)
        )
        health_status["checks"]["negative_points_users"] = negative_count
    except Exception as e:
        health_status["checks"]["db"] = f"error: {e}"

    return health_status
```

---

## 十一、测试策略

### 11.1 单元测试

```python
# tests/services/test_ability_service.py

@pytest.mark.asyncio
async def test_add_points_sync():
    """测试同步增加能力值"""
    service = AbilityService()

    log = await service.add_points(
        user_id="test_user",
        action_type="salary.created",
        points=10,
        is_sync=True
    )

    assert log.points_change == 10
    assert log.action_type == "salary.created"

@pytest.mark.asyncio
async def test_daily_limit():
    """测试每日限制"""
    service = AbilityService()

    # 连续发帖 10 次（正常）
    for _ in range(10):
        await service.add_points(
            user_id="test_user",
            action_type="post.created",
            points=20
        )

    # 第 11 次应该抛出异常
    with pytest.raises(DailyLimitExceeded):
        await service.add_points(
            user_id="test_user",
            action_type="post.created",
            points=20
        )

@pytest.mark.asyncio
async def test_deduct_points_below_zero():
    """测试扣减到负数"""
    service = AbilityService()

    # 用户只有 50 能力值，扣减 100
    log = await service.deduct_points(
        user_id="test_user",
        action_type="admin.penalty",
        points=100,
        reason="刷量处罚"
    )

    assert log.points_change == -100
    # 验证用户能力值为 -50
    user = await service._get_user("test_user")
    assert user.ability_points == -50
```

### 11.2 集成测试

```python
# tests/integration/test_ability_integration.py

@pytest.mark.asyncio
async def test_post_create_flow():
    """测试发帖完整流程（事件发布 → 能力值增加 → 排行榜更新）"""
    # 1. 发帖
    post = await post_service.create_post(
        user_id="test_user",
        content="测试帖子"
    )

    # 2. 等待 Celery 任务完成
    await asyncio.sleep(1)

    # 3. 验证能力值增加
    user = await get_user("test_user")
    assert user.ability_points >= 20

    # 4. 验证日志记录
    logs = await ability_service.get_user_logs("test_user", limit=1)
    assert logs[0].action_type == "post.created"

    # 5. 验证排行榜更新
    rank = await leaderboard_service.get_user_rank("test_user")
    assert rank is not None
```

---

## 十二、部署指南

### 12.1 数据库迁移顺序

```bash
# 1. 添加 users 表字段（已在 Sprint 4.1 完成）
alembic upgrade head

# 2. 创建能力值日志表
alembic revision --autogenerate -m "add ability_points_logs table"
alembic upgrade head

# 3. 创建每日统计表
alembic revision --autogenerate -m "add daily_action_counts table"
alembic upgrade head
```

### 12.2 Redis 初始化

```python
# scripts/init_ability_system.py

async def init_ability_system():
    """初始化能力值系统"""

    # 1. 为现有用户初始化能力值（根据历史行为）
    users = await db.execute(select(User))
    for user in users:
        # 计算历史能力值
        historical_points = await calculate_historical_points(user.id)
        user.ability_points = historical_points
        user.ability_level = calculate_level(historical_points)

    await db.commit()

    # 2. 初始化排行榜（根据现有用户能力值）
    redis.delete("leaderboard:ability_points:total")
    for user in users:
        await redis.zadd(
            "leaderboard:ability_points:total",
            {user.id: user.ability_points}
        )

    print("能力值系统初始化完成")
```

### 12.3 Celery Worker 配置

```python
# celeryconfig.py

celery_conf = {
    "task_routes": {
        "app.tasks.ability_tasks.process_ability_event": {
            "queue": "ability_points",  # 专用队列
            "rate_limit": "100/m",      # 限流
        }
    },
    "task_soft_time_limit": 30,  # 软超时
    "task_time_limit": 60,       # 硬超时
}
```

---

## 十三、总结

### 13.1 设计要点

1. **混合模式**：关键操作用事务，普通操作用异步，平衡性能与一致性
2. **事件驱动**：完全解耦，易于扩展和监控
3. **复用 Celery**：利用现有基础设施，降低复杂度
4. **Redis+DB 混合**：性能与持久化兼顾
5. **完整扣减系统**：支持负数能力值，等级可下降，完整奖惩体系
6. **每日限制**：Redis 实时检查，定时同步到数据库
7. **排行榜**：4 个榜单，Redis ZSet 实现
8. **完整日志**：所有能力值变化可追溯
9. **监控告警**：关键指标、健康检查
10. **易于集成**：最小化修改现有代码

### 13.2 后续工作

本设计文档已获批准，下一步将调用 `writing-plans` skill 创建详细的实现计划，包括：

1. 文件创建清单（backend/app/services/ability_service.py 等）
2. 数据库迁移脚本
3. Celery 任务实现
4. API 路由实现
5. 前端集成（API clients、stores、组件）
6. 测试用例清单
7. 部署步骤

---

**文档结束**
