# 数据库索引优化

本文档记录了为提高查询性能而添加的数据库索引。

## 索引添加原则

1. **为常用查询条件添加索引**
2. **为排序字段添加索引**
3. **为外键添加索引**
4. **复合索引遵循最左前缀原则**

## 已添加的索引

### User 表
```sql
-- 索引：匿名昵称查询
CREATE INDEX idx_user_anonymous_name ON user(anonymous_name);

-- 索引：状态筛选
CREATE INDEX idx_user_status ON user(status);

-- 索引：创建时间排序
CREATE INDEX idx_user_created_at ON user(created_at DESC);
```

### Post 表
```sql
-- 索引：用户帖子查询
CREATE INDEX idx_post_user_id_status ON post(user_id, status, risk_status);

-- 索引：热门帖子排序
CREATE INDEX idx_post_like_count ON post(like_count DESC, created_at DESC);

-- 索引：风险状态筛选
CREATE INDEX idx_post_risk_status ON post(risk_status);

-- 索引：状态筛选
CREATE INDEX idx_post_status ON post(status, created_at DESC);
```

### Comment 表
```sql
-- 索引：帖子评论查询
CREATE INDEX idx_comment_post_id ON comment(post_id, created_at ASC);

-- 索引：用户评论查询
CREATE INDEX idx_comment_user_id ON comment(user_id);
```

### Follow 表
```sql
-- 索引：关注关系查询
CREATE INDEX idx_follow_follower ON follow(follower_id, is_deleted);
CREATE INDEX idx_follow_following ON follow(following_id, is_deleted);

-- 唯一索引：防止重复关注
CREATE UNIQUE INDEX idx_follow_unique ON follow(follower_id, following_id) WHERE is_deleted = false;
```

### Like 表
```sql
-- 索引：点赞状态查询
CREATE INDEX idx_like_target ON like(target_type, target_id, user_id);
```

### SalaryRecord 表
```sql
-- 索引：用户薪资查询
CREATE INDEX idx_salary_user_id ON salary_record(user_id, payday_date DESC);

-- 索引：发薪日配置查询
CREATE INDEX idx_salary_config_id ON salary_record(config_id);
```

### PaydayConfig 表
```sql
-- 索引：用户配置查询
CREATE INDEX idx_payday_user_id ON payday_config(user_id, created_at);
```

### MembershipOrder 表
```sql
-- 索引：用户订单查询
CREATE INDEX idx_membership_order_user ON membership_order(user_id, created_at DESC);

-- 索引：状态筛选
CREATE INDEX idx_membership_order_status ON membership_order(status);
```

### Notification 表
```sql
-- 索引：用户通知查询
CREATE INDEX idx_notification_user_unread ON notification(user_id, is_read, created_at DESC);
```

## Alembic 迁移脚本

要将这些索引应用到数据库，创建以下迁移：

```python
# alembic/versions/xxx_add_performance_indexes.py

from alembic import op
import sqlalchemy as sa


def upgrade():
    # User indexes
    op.create_index('idx_user_anonymous_name', 'user', ['anonymous_name'])
    op.create_index('idx_user_status', 'user', ['status'])
    op.create_index('idx_user_created_at', 'user', [sa.text('created_at DESC')])

    # Post indexes
    op.create_index('idx_post_user_id_status', 'post', ['user_id', 'status', 'risk_status'])
    op.create_index('idx_post_like_count', 'post', [sa.text('like_count DESC, created_at DESC')])
    op.create_index('idx_post_risk_status', 'post', ['risk_status'])
    op.create_index('idx_post_status', 'post', ['status', sa.text('created_at DESC')])

    # Comment indexes
    op.create_index('idx_comment_post_id', 'comment', ['post_id', sa.text('created_at ASC')])
    op.create_index('idx_comment_user_id', 'comment', ['user_id'])

    # Follow indexes
    op.create_index('idx_follow_follower', 'follow', ['follower_id', 'is_deleted'])
    op.create_index('idx_follow_following', 'follow', ['following_id', 'is_deleted'])
    # 注意：条件索引在 MySQL 中可能需要调整语法

    # Like indexes
    op.create_index('idx_like_target', 'like', ['target_type', 'target_id', 'user_id'])

    # SalaryRecord indexes
    op.create_index('idx_salary_user_id', 'salary_record', ['user_id', sa.text('payday_date DESC')])
    op.create_index('idx_salary_config_id', 'salary_record', ['config_id'])

    # PaydayConfig indexes
    op.create_index('idx_payday_user_id', 'payday_config', ['user_id', 'created_at'])

    # MembershipOrder indexes
    op.create_index('idx_membership_order_user', 'membership_order', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_membership_order_status', 'membership_order', ['status'])

    # Notification indexes
    op.create_index('idx_notification_user_unread', 'notification', ['user_id', 'is_read', sa.text('created_at DESC')])


def downgrade():
    # User indexes
    op.drop_index('idx_user_anonymous_name', 'user')
    op.drop_index('idx_user_status', 'user')
    op.drop_index('idx_user_created_at', 'user')

    # Post indexes
    op.drop_index('idx_post_user_id_status', 'post')
    op.drop_index('idx_post_like_count', 'post')
    op.drop_index('idx_post_risk_status', 'post')
    op.drop_index('idx_post_status', 'post')

    # Comment indexes
    op.drop_index('idx_comment_post_id', 'comment')
    op.drop_index('idx_comment_user_id', 'comment')

    # Follow indexes
    op.drop_index('idx_follow_follower', 'follow')
    op.drop_index('idx_follow_following', 'follow')

    # Like indexes
    op.drop_index('idx_like_target', 'like')

    # SalaryRecord indexes
    op.drop_index('idx_salary_user_id', 'salary_record')
    op.drop_index('idx_salary_config_id', 'salary_record')

    # PaydayConfig indexes
    op.drop_index('idx_payday_user_id', 'payday_config')

    # MembershipOrder indexes
    op.drop_index('idx_membership_order_user', 'membership_order')
    op.drop_index('idx_membership_order_status', 'membership_order')

    # Notification indexes
    op.drop_index('idx_notification_user_unread', 'notification')
```

## 运行迁移

```bash
cd backend

# 生成迁移文件
alembic revision -m "add_performance_indexes"

# 将上述代码复制到生成的迁移文件中

# 执行迁移
alembic upgrade head
```

## 性能验证

添加索引后，使用以下命令验证性能：

```sql
-- 查看表的索引
SHOW INDEX FROM post;
SHOW INDEX FROM comment;
SHOW INDEX FROM follow;

-- 分析查询执行计划
EXPLAIN SELECT * FROM post WHERE user_id = 'xxx' AND status = 'normal' ORDER BY created_at DESC;
```

## 注意事项

1. **索引会降低写入性能** - 只为真正需要的查询添加索引
2. **定期维护索引** - 使用 `ANALYZE TABLE` 更新统计信息
3. **监控慢查询** - 定期检查慢查询日志，优化必要索引
