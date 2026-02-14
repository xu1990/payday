# 开发文档

## 目录

- [架构概览](#架构概览)
- [后端开发](#后端开发)
- [前端开发](#前端开发)
- [数据库管理](#数据库管理)
- [部署指南](#部署指南)
- [故障排查](#故障排查)

---

## 架构概览

### 技术栈

| 组件 | 技术栈 | 说明 |
|------|--------|--------|
| **Backend** | FastAPI + Python 3.11 | 异步 Python Web 框架 |
| **Database** | MySQL 8.0+ | 主数据存储 |
| **Cache** | Redis 6+ | 缓存和消息队列 |
| **Tasks** | Celery | 异步任务处理 |
| **Admin** | Vue 3 + Element Plus | 管理后台 |
| **Miniapp** | uni-app + Vue 3 | 微信小程序 |

### 数据流

```
┌─────────────┐
│  Miniapp  │  微信小程序
└─────┬─────┘
      │
      ▼
┌─────────────────┐
│  FastAPI       │  Backend REST API
│  + SQLAlchemy  │
└─────┬─────────┘
      │
      ├────────────┬────────────┐
      ▼            ▼            ▼
┌──────────┐  ┌─────────┐  ┌────────┐
│  MySQL   │  │  Redis   │  │ Celery  │
│          │  │         │  │ Worker  │
└──────────┘  └─────────┘  └─────────┘
      │            │            │
      └────────────┴────────────┘
                  ▼
         ┌──────────────┐
         │ Admin-Web   │  管理后台
         └──────────────┘
```

---

## 后端开发

### 目录结构

```
backend/app/
├── api/v1/           # API 路由层
│   ├── auth.py      # 认证端点
│   ├── users.py     # 用户管理
│   └── ...
├── core/             # 核心配置
│   ├── config.py     # 设置和验证
│   ├── database.py  # 数据库连接
│   ├── security.py  # JWT 认证
│   └── deps.py      # 依赖注入
├── models/           # ORM 模型
│   ├── base.py      # Base 模型
│   ├── user.py      # 用户模型
│   └── ...
├── schemas/          # Pydantic schemas
│   ├── user.py
│   └── ...
├── services/         # 业务逻辑
│   ├── auth_service.py
│   └── ...
├── utils/            # 工具函数
│   ├── encryption.py  # 薪资加密
│   └── ...
└── tasks/           # Celery 任务
    ├── risk_check.py
    └── ...
```

### 创建新 API 端点

#### 1. 定义 Schema

`app/schemas/post.py`:

```python
from pydantic import BaseModel
from typing import Optional

class PostCreate(BaseModel):
    """创建帖子的请求模型"""
    content: str
    images: list[str] = []
    tags: list[str] = []
    mood: str

class PostResponse(BaseModel):
    """帖子响应模型"""
    id: str
    content: str
    images: list[str]
    tags: list[str]
    mood: str
    created_at: datetime
    author: UserSummary
```

#### 2. 实现业务逻辑

`app/services/post_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.post import Post
from app.schemas.post import PostCreate

async def create_post(
    db: AsyncSession,
    user_id: str,
    data: PostCreate
) -> Post:
    """创建帖子"""
    post = Post(
        user_id=user_id,
        content=data.content,
        images=data.images,
        tags=data.tags,
        mood=data.mood,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post
```

#### 3. 添加路由

`app/api/v1/post.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.services.post_service import create_post
from app.schemas.post import PostCreate

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/")
async def create(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await create_post(db, current_user.id, data)
```

#### 4. 注册路由

`app/api/v1/__init__.py`:

```python
from fastapi import APIRouter

from app.api.v1 import post

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(post.router)
```

### 数据库迁移

#### 创建迁移

```bash
# 生成迁移脚本
python3 -m alembic revision --autogenerate -m "add post table"

# 查看生成的迁移文件
# 编辑以调整 SQL（如需要）

# 应用迁移
python3 -m alembic upgrade head
```

#### 回滚迁移

```bash
# 回滚一个版本
python3 -m alembic downgrade -1

# 回滚到特定版本
python3 -m alembic downgrade <revision_id>
```

### 异步任务

#### 定义任务

`app/tasks/scheduled.py`:

```python
from celery import shared_task

@shared_task(name="payday.reminder")
def send_payday_reminders():
    """发送发薪日提醒"""
    # 业务逻辑
    pass
```

#### 定时任务

`app/tasks/beat.py`:

```python
from celery.schedules import crontab

beat_config = {
    "payday.reminder": {
        "task": "payday.reminder",
        "schedule": crontab(hour="9", minute=0),  # 每天 9:00
    },
}
```

---

## 前端开发

### Admin-Web 架构

```
src/
├── api/          # API 客户端模块
│   ├── admin.ts
│   └── request.ts
├── components/   # 可复用组件
│   ├── BaseDataTable.vue
│   └── ...
├── stores/       # Pinia stores
│   ├── auth.ts
│   └── user.ts
├── views/        # 页面组件
│   └── users/
│       └── List.vue
└── utils/        # 工具函数
    └── request.ts
```

### API 调用

#### 定义 API 客户端

`src/api/admin.ts`:

```typescript
import request from '@/utils/request'

export interface User {
  id: string
  username: string
  email: string
  role: string
}

export function listUsers(params?: {
  limit?: number
  offset?: number
}) {
  return request<UserListResult>({
    url: '/admin/users',
    method: 'GET',
    params,
  })
}
```

#### 使用 Store

`src/stores/auth.ts`:

```typescript
import { defineStore } from 'pinia'
import { login as apiLogin } from '@/api/admin'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: '',
  }),

  actions: {
    async login(username: string, password: string) {
      const data = await apiLogin(username, password)
      this.user = data.user
      this.accessToken = data.accessToken
    },
  },
})
```

### Miniapp 架构

```
src/
├── api/          # API 客户端
├── components/   # 组件
│   ├── LazyImage.vue
│   └── ...
├── pages/        # 页面
│   └── index/
├── stores/       # Pinia stores
│   ├── auth.ts
│   └── post.ts
└── utils/        # 工具函数
    ├── request.ts
    └── error.ts
```

### 页面路由

`pages.json`:

```json
{
  "pages": [
    "pages/index/index",
    "pages/user/home",
    "pages/post/detail"
  ],
  "tabBar": {
    "list": [
      { "pagePath": "pages/index/index", "text": "首页", "iconPath": "static/home.png" },
      { "pagePath": "pages/square/index", "text": "广场", "iconPath": "static/square.png" }
    ]
  }
}
```

---

## 数据库管理

### 连接数据库

```bash
# MySQL
mysql -h 127.0.0.1 -u payday -p

# 使用配置文件
mysql --defaults-file=~/.my.cnf
```

### 常用操作

```sql
-- 查看表结构
DESCRIBE users;

-- 查看索引
SHOW INDEX FROM users;

-- 分析查询
EXPLAIN SELECT * FROM posts WHERE user_id = 'xxx';

-- 查看慢查询
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;
```

### 备份与恢复

```bash
# 备份
mysqldump -u root -p payday > backup_$(date +%Y%m%d).sql

# 恢复
mysql -u root -p payday < backup_20260214.sql
```

---

## 部署指南

### 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 6+
- Nginx (可选)

### Backend 部署

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 运行迁移
python3 -m alembic upgrade head

# 3. 创建管理员用户
python3 scripts/create_first_admin.py

# 4. 使用 Gunicorn 启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 前端部署

```bash
# Admin-Web
cd admin-web
npm run build

# Miniapp
cd miniapp
npm run build
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name payday.example.com;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Admin Web
    location /admin {
        alias /path/to/admin-web/dist/;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 故障排查

### Backend

**问题**: `ModuleNotFoundError: No module named 'app'`

**解决**:
```bash
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

**问题**: 数据库连接失败

**排查**:
```bash
# 检查 MySQL 状态
systemctl status mysql

# 测试连接
mysql -h 127.0.0.1 -u payday -p

# 检查 .env 配置
```

### Frontend

**问题**: `Cannot find module '@/components'`

**解决**:
```typescript
// 检查 vite.config.ts alias
alias: {
  '@': '/src',
}
```

**问题**: API 请求 CORS 错误

**解决**:
```python
# 检查 backend/.env CORS_ORIGINS
CORS_ORIGINS=https://yourdomain.com
```

### 性能问题

**慢 API**:
```bash
# 开发环境 SQL 日志
SQLALCHEMY_ECHO=true

# 使用 EXPLAIN 分析
```

**内存泄漏**:
```bash
# 检查 Redis 内存
redis-cli INFO memory

# 检查 Celery 队列
celery -A app.tasks.worker inspect active
```

---

## 开发工具推荐

- **IDE**: VSCode / PyCharm
- **API 测试**: Postman / Insomnia
- **数据库**: MySQL Workbench / DBeaver
- **Redis**: RedisInsight
- **Git**: GitKraken / SourceTree

---

**更新日期**: 2026-02-14
**版本**: 1.0.0
