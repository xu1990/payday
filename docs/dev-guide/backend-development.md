# Backend 开发文档

## 项目概述

薪日 PayDay 后端服务是基于 FastAPI 构建的高性能异步 API 服务，为微信小程序和管理后台提供 RESTful API 接口。

### 技术栈

- **框架**: FastAPI 0.104.0+
- **Python版本**: 3.11+ (CI 支持 3.9+)
- **数据库**: MySQL 8.0+ (生产) / SQLite (开发)
- **ORM**: SQLAlchemy 2.0+ (异步)
- **缓存**: Redis 5.0+
- **任务队列**: Celery 5.3+
- **认证**: JWT (python-jose)
- **API文档**: OpenAPI/Swagger

---

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+ 或 SQLite
- Redis 6.0+

### 安装步骤

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库、Redis等

# 运行数据库迁移
python3 -m alembic upgrade head

# 创建管理员账户
python3 scripts/create_first_admin.py

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问 API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/              # API 路由处理器
│   │       ├── auth.py      # 认证接口
│   │       ├── users.py     # 用户管理
│   │       ├── payday.py    # 发薪日配置
│   │       ├── salary.py    # 薪资记录
│   │       ├── posts.py     # 社区帖子
│   │       ├── comments.py  # 评论
│   │       ├── likes.py     # 点赞
│   │       ├── follows.py   # 关注
│   │       ├── admin/       # 管理后台接口
│   │       └── ...
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── security.py      # 安全工具
│   │   ├── deps.py          # 依赖注入
│   │   ├── exceptions.py    # 异常定义
│   │   └── error_handler.py # 异常处理
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── base.py          # 基础模型
│   │   ├── user.py          # 用户模型
│   │   ├── salary.py        # 薪资模型
│   │   └── ...
│   ├── schemas/             # Pydantic 验证模式
│   │   ├── user.py
│   │   ├── salary.py
│   │   └── ...
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── ...
│   ├── tasks/               # Celery 异步任务
│   │   ├── risk_check.py    # 内容审核
│   │   └── scheduled.py     # 定时任务
│   ├── utils/               # 工具函数
│   │   ├── encryption.py    # 加密工具
│   │   ├── wechat.py        # 微信接口
│   │   └── ...
│   └── main.py              # 应用入口
├── alembic/                 # 数据库迁移
│   ├── versions/            # 迁移版本
│   └── env.py
├── scripts/                 # 工具脚本
│   ├── create_first_admin.py
│   ├── generate_secrets.py
│   └── ...
├── tests/                   # 测试文件
├── requirements.txt         # 生产依赖
├── requirements-dev.txt     # 开发依赖
└── .env.example             # 环境变量模板
```

---

## 核心设计模式

### 1. Service Layer Pattern

业务逻辑封装在 `app/services/` 中，API 路由保持简洁：

```python
# app/api/v1/users.py
from app.services.user_service import UserService

@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    return await UserService.get_user_profile(db, current_user.id)
```

### 2. 依赖注入

使用 `app/core/deps.py` 提供常用依赖：

```python
from app.core.deps import get_db, get_current_user, get_current_admin

# 数据库会话
@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    ...

# 当前用户
@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    ...

# 管理员权限
@router.delete("/admin/users/{id}")
async def delete_user(
    id: str,
    admin: User = Depends(get_current_admin)
):
    ...
```

### 3. Pydantic Schemas

所有 API 输入/输出使用 Pydantic 验证：

```python
# app/schemas/user.py
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)
    avatar: str | None = None

class UserResponse(BaseModel):
    id: str
    nickname: str
    avatar: str | None
    created_at: datetime

    class Config:
        from_attributes = True
```

### 4. 异常处理

使用统一异常体系：

```python
from app.core.exceptions import (
    BusinessException,
    NotFoundException,
    ValidationException,
    error_response,
    success_response
)

# 抛出异常
raise NotFoundException("用户不存在")
raise ValidationException("参数错误", details={"field": "nickname"})
raise BusinessException("操作不允许", code="OPERATION_NOT_ALLOWED")

# 返回结构化响应
return error_response(400, "创建失败", code="CREATE_FAILED")
return success_response(data={"id": 123}, message="创建成功")
```

---

## 数据库操作

### 异步数据库会话

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "添加新字段"

# 应用迁移
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看迁移历史
alembic history
```

---

## 认证与授权

### 微信小程序登录

```python
# 小程序通过 code 换取 openid，然后生成 JWT
@router.post("/auth/login")
async def login(code: str, db: AsyncSession = Depends(get_db)):
    # 1. code 换 openid
    openid = await wechat_service.code2session(code)

    # 2. 查找或创建用户
    user = await UserService.get_or_create_by_openid(db, openid)

    # 3. 生成 JWT
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

### 管理员认证

管理员使用用户名密码登录，JWT 中包含 `scope: admin`：

```python
@router.post("/admin/login")
async def admin_login(credentials: AdminLogin, db: AsyncSession = Depends(get_db)):
    admin = await authenticate_admin(db, credentials.username, credentials.password)
    if not admin:
        raise AuthenticationException("用户名或密码错误")

    token = create_access_token({
        "sub": admin.id,
        "scope": "admin",
        "role": admin.role
    })
    return {"access_token": token}
```

### 权限控制

```python
from app.core.deps import require_permission

# 需要 admin 角色
@router.put("/admin/config")
async def update_config(
    _perm: bool = Depends(require_permission("admin"))
):
    ...

# 需要 superadmin 角色
@router.delete("/admin/users/{id}")
async def delete_user(
    _perm: bool = Depends(require_permission("superadmin"))
):
    ...
```

---

## 安全特性

### 薪资数据加密

薪资金额使用 HKDF + Fernet 对称加密：

```python
from app.utils.encryption import encryption_service

# 加密
encrypted = encryption_service.encrypt_amount(10000.00)

# 解密
decrypted = encryption_service.decrypt_amount(encrypted)
```

### CSRF 保护

管理后台接口需要 CSRF 验证：

```python
from app.core.deps import verify_csrf_token

@router.post("/admin/data")
async def create_data(
    _csrf: bool = Depends(verify_csrf_token)
):
    ...
```

### 请求限流

```python
from app.core.deps import rate_limit_login, rate_limit_post

# 登录限流: 5次/分钟
@router.post("/auth/login")
async def login(_rate: bool = Depends(rate_limit_login)):
    ...

# 发帖限流: 10次/分钟
@router.post("/posts")
async def create_post(_rate: bool = Depends(rate_limit_post)):
    ...
```

---

## 异步任务

### Celery 配置

```bash
# 启动 Worker
celery -A app.celery_app.celery worker -l info

# 启动 Beat (定时任务)
celery -A app.celery_app.celery beat -l info

# 启动 Flower (监控)
celery -A app.celery_app.celery flower --port=5555
```

### 定义任务

```python
# app/tasks/risk_check.py
from app.celery_app.celery import celery_app

@celery_app.task
def check_content_risk(content: str, content_type: str, target_id: str):
    """内容风险检测"""
    result = tencent_yu.check_text(content)
    if result["risk"]:
        # 处理违规内容
        handle_risky_content(content_type, target_id)
```

### 调用任务

```python
from app.tasks.risk_check import check_content_risk

# 异步调用
check_content_risk.delay(post.content, "post", post.id)
```

---

## 缓存策略

```python
from app.core.database import redis_client

# 用户信息缓存 (1小时)
await redis_client.setex(
    f"user:info:{user_id}",
    3600,
    json.dumps(user_data)
)

# 发薪日状态缓存 (1天)
await redis_client.setex(
    f"payday:status:{user_id}:{date}",
    86400,
    status
)

# 热门帖子 (Sorted Set, 24小时)
await redis_client.zadd(
    f"post:hot:{date}",
    {post_id: score}
)
await redis_client.expire(f"post:hot:{date}", 86400)
```

---

## API 路由结构

| 路由前缀 | 功能 | 权限 |
|---------|------|------|
| `/api/v1/auth/*` | 认证登录 | 公开 |
| `/api/v1/users/*` | 用户管理 | 用户 |
| `/api/v1/payday/*` | 发薪日配置 | 用户 |
| `/api/v1/salary/*` | 薪资记录 | 用户 |
| `/api/v1/posts/*` | 社区帖子 | 用户 |
| `/api/v1/comments/*` | 评论 | 用户 |
| `/api/v1/likes/*` | 点赞 | 用户 |
| `/api/v1/follows/*` | 关注 | 用户 |
| `/api/v1/notifications/*` | 通知 | 用户 |
| `/api/v1/admin/*` | 管理后台 | 管理员 |
| `/api/v1/payment/*` | 支付 | 用户 |

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行单个测试文件
pytest tests/test_auth.py

# 运行单个测试函数
pytest tests/test_auth.py::test_login

# 排除慢测试
pytest -m "not slow"

# 只运行单元测试
pytest -m "unit"

# 只运行集成测试
pytest -m "integration"
```

### 测试标记

- `slow` - 慢测试
- `integration` - 集成测试
- `unit` - 单元测试
- `asyncio` - 异步测试

### 编写测试

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={
            "code": "test_code"
        })
        assert response.status_code == 200
```

---

## 代码规范

### 代码风格

- 遵循 PEP 8
- 使用类型注解
- 使用 Black 格式化
- 使用 isort 排序导入

### 运行代码检查

```bash
# 从项目根目录运行
npm run lint:backend     # Pylint
npm run format:backend   # Black + isort
```

### Git 提交规范

使用 Conventional Commits:

```
feat(auth): 添加手机号登录功能
fix(salary): 修复薪资加密问题
docs(api): 更新 API 文档
test(user): 添加用户服务测试
refactor(cache): 重构缓存逻辑
```

---

## 常用脚本

### 生成密钥

```bash
python3 scripts/generate_secrets.py
```

### 创建管理员

```bash
# 使用环境变量指定密码
ADMIN_DEFAULT_PASSWORD=your_password python3 scripts/create_first_admin.py
```

### 诊断工具

```bash
python3 scripts/diagnose_splash_endpoint.py
```

---

## 环境变量

完整的环境变量配置见 `.env.example`：

| 变量名 | 说明 | 必填 |
|-------|------|-----|
| `DATABASE_URL` | 数据库连接串 | 是 |
| `REDIS_URL` | Redis 连接串 | 是 |
| `JWT_SECRET_KEY` | JWT 密钥 (32+字节) | 是 |
| `ENCRYPTION_SECRET_KEY` | 加密密钥 (32字节) | 是 |
| `WECHAT_APP_ID` | 微信小程序 AppID | 是 |
| `WECHAT_APP_SECRET` | 微信小程序 Secret | 是 |
| `WECHAT_MCH_ID` | 微信支付商户号 | 否 |
| `COS_SECRET_ID` | 腾讯云 COS ID | 否 |
| `COS_SECRET_KEY` | 腾讯云 COS Key | 否 |
| `TENCENT_SECRET_ID` | 腾讯云天御 ID | 否 |
| `TENCENT_SECRET_KEY` | 腾讯云天御 Key | 否 |
| `CORS_ORIGINS` | CORS 允许源 | 否 |

---

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 MySQL 服务是否启动
   - 检查 `DATABASE_URL` 配置
   - 检查网络连接

2. **Redis 连接失败**
   - 检查 Redis 服务是否启动
   - 检查 `REDIS_URL` 配置

3. **迁移失败**
   - 检查数据库权限
   - 尝试 `alembic downgrade` 后重新升级

4. **JWT 验证失败**
   - 检查 `JWT_SECRET_KEY` 是否正确
   - 检查 token 是否过期

5. **微信登录失败**
   - 检查 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
   - 检查网络是否能访问微信 API
