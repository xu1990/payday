# PayDay Backend API

薪日 PayDay 后端服务 - 基于 FastAPI 构建的微信小程序后端 API。

## 技术栈

- **Python**: 3.11+ (CI 支持 3.9+)
- **Web 框架**: FastAPI
- **数据库**: MySQL 8.0+
- **缓存**: Redis
- **ORM**: SQLAlchemy (Async)
- **数据库迁移**: Alembic
- **异步任务**: Celery + Redis
- **数据验证**: Pydantic
- **认证**: JWT
- **对象存储**: 腾讯云 COS
- **内容审核**: 腾讯云天御
- **支付**: 微信支付

## 项目结构

```
backend/
├── app/
│   ├── api/v1/              # API 路由
│   │   ├── auth.py          # 认证相关
│   │   ├── users.py         # 用户管理
│   │   ├── payday.py        # 薪日配置
│   │   ├── salary.py        # 薪资记录
│   │   ├── post.py          # 帖子
│   │   ├── comment.py       # 评论
│   │   ├── like.py          # 点赞
│   │   ├── follow.py        # 关注
│   │   ├── notification.py  # 通知
│   │   ├── statistics.py    # 统计
│   │   ├── membership.py    # 会员
│   │   ├── payment.py       # 支付
│   │   └── admin_*.py       # 管理后台
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置
│   │   ├── database.py      # 数据库
│   │   ├── security.py      # 安全认证
│   │   ├── deps.py          # 依赖注入
│   │   ├── exceptions.py    # 异常定义
│   │   └── error_handler.py # 错误处理
│   ├── models/              # ORM 模型
│   ├── schemas/             # Pydantic 验证模式
│   ├── services/            # 业务逻辑层
│   ├── tasks/               # Celery 异步任务
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── scripts/                 # 工具脚本
├── requirements.txt         # 依赖
├── requirements-dev.txt     # 开发依赖
└── .env                     # 环境变量
```

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+

### 安装依赖

```bash
# 开发环境
pip install -r requirements-dev.txt

# 生产环境
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

关键配置项：

```env
# MySQL 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=payday

# Redis
REDIS_URL=redis://localhost:6379/0

# 微信小程序
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# 微信支付
WECHAT_MCH_ID=your_mch_id
WECHAT_PAY_API_KEY=your_api_key
WECHAT_PAY_NOTIFY_URL=https://your-domain.com/api/v1/payment/wechat/notify

# JWT 密钥
JWT_SECRET_KEY=your_secret_key

# 加密密钥 (32字节)
ENCRYPTION_SECRET_KEY=your_32_byte_encryption_key

# 腾讯云 COS
COS_SECRET_ID=your_secret_id
COS_SECRET_KEY=your_secret_key
COS_REGION=ap-guangzhou
COS_BUCKET=your_bucket

# 腾讯云天御 (内容审核)
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 创建管理员账号

```bash
python3 scripts/create_first_admin.py
```

### 启动服务

```bash
# 开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 启动 Celery

```bash
# Worker
celery -A app.tasks.worker -l info

# Beat (定时任务)
celery -A app.tasks.beat -l info
```

## API 文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要 API 端点

### 认证 `/api/v1/auth`

- `POST /login` - 微信小程序登录
- `POST /admin/login` - 管理后台登录
- `POST /refresh` - 刷新 Token

### 用户 `/api/v1/users`

- `GET /me` - 获取当前用户信息
- `PUT /me` - 更新用户信息
- `GET /{user_id}` - 获取用户详情

### 薪日 `/api/v1/payday`

- `GET /` - 获取薪日配置
- `POST /` - 设置薪日
- `GET /status` - 获取薪日状态
- `POST /next` - 设置下一个薪日

### 薪资 `/api/v1/salary`

- `POST /` - 创建薪资记录
- `GET /` - 获取薪资列表
- `GET /stats` - 获取薪资统计

### 社区 `/api/v1/posts`, `/api/v1/comments`, `/api/v1/likes`

- 帖子发布、列表、详情
- 评论创建、列表
- 点赞/取消点赞

### 会员 `/api/v1/membership`

- `GET /` - 获取会员配置
- `POST /purchase` - 购买会员

### 支付 `/api/v1/payment`

- `POST /wechat/create` - 创建微信支付订单
- `POST /wechat/notify` - 微信支付回调

### 管理后台 `/api/v1/admin/*`

需要 `scope=admin` 的 JWT Token。

## 核心设计模式

### Service Layer Pattern

业务逻辑位于 `app/services/`，API 路由层保持简洁：

```python
# app/services/salary_service.py
class SalaryService:
    async def create_salary(self, user_id: int, amount: int) -> Salary:
        # 业务逻辑
        ...

# app/api/v1/salary.py
@router.post("/")
async def create_salary(
    salary_data: SalaryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await salary_service.create_salary(current_user.id, salary_data.amount)
```

### 依赖注入

使用 `app/core/deps.py` 提供的依赖：

```python
from app.core.deps import get_db, get_current_user, get_current_admin

@router.get("/")
async def get_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...
```

### 异常处理

使用自定义异常和统一错误响应：

```python
from app.core.exceptions import BusinessException, NotFoundException

# 抛出异常
raise NotFoundException("用户不存在")

# 自定义错误响应
from app.core.exceptions import error_response
return error_response(
    status_code=400,
    message="创建失败",
    code="CREATE_FAILED"
)
```

### 数据加密

薪资金额加密存储：

```python
from app.utils.encryption import encryption_service

# 加密存储
encrypted = encryption_service.encrypt_amount(amount)

# 解密读取
decrypted = encryption_service.decrypt_amount(encrypted)
```

## 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_specific_file.py

# 运行特定测试函数
pytest tests/test_specific_file.py::test_function_name

# 排除慢速测试
pytest -m "not slow"

# 只运行集成测试
pytest tests/integration/ -v
```

测试标记：
- `slow` - 慢速测试
- `integration` - 集成测试
- `unit` - 单元测试
- `asyncio` - 异步测试

## 代码规范

```bash
# Lint (从根目录运行)
cd .. && npm run lint:backend    # Pylint

# Format (从根目录运行)
cd .. && npm run format:backend  # Black + isort
```

- 遵循 PEP 8
- 使用类型提示 (mypy strict mode)
- 函数文档字符串

## 缓存策略

- `user:info:{user_id}` - 用户信息 (1h TTL)
- `payday:status:{user_id}:{date}` - 薪日状态 (1d TTL)
- `post:hot:{date}` - 热门帖子 (Sorted Set, 24h TTL)
- `like:status:{user_id}:{type}:{id}` - 点赞状态 (7d TTL)

## 安全特性

- **薪资加密**: 使用 AES-256-GCM 加密存储
- **JWT 认证**: 双 Token 机制 (Access + Refresh)
- **Rate Limiting**: 基于 Redis 的 API 限流
- **CSRF 保护**: 关键操作验证 CSRF Token
- **签名验证**: API 请求签名验证
- **内容审核**: 集成腾讯云天御
- **敏感词过滤**: 本地敏感词库

## 异步任务

使用 Celery 处理：

- 内容风控审核 (`app/tasks/risk_check.py`)
- 定时通知 (`app/tasks/scheduled.py`)
- 统计计算

## 监控与日志

- **结构化日志**: JSON 格式输出
- **Sentry 集成**: 错误追踪 (`app/utils/sentry.py`)
- **指标收集**: Prometheus 格式 (`app/utils/metrics.py`)

## 部署注意事项

1. 运行数据库迁移
2. 创建至少一个管理员账号
3. 配置 Nginx 反向代理
4. 启动 Celery Worker 和 Beat
5. 配置 HTTPS (生产环境)

## 故障排查

### 常见问题

**数据库连接失败**
- 检查 `.env` 中的数据库配置
- 确保 MySQL 服务运行

**Redis 连接失败**
- 检查 `REDIS_URL` 配置
- 确保 Redis 服务运行

**微信登录失败**
- 检查 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
- 确认小程序已开通登录功能

**支付回调失败**
- 检查 `WECHAT_PAY_NOTIFY_URL` 是否可访问
- 确认商户配置正确

## 开发资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [Celery 文档](https://docs.celeryproject.org/)
