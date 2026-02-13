# 综合测试覆盖设计文档

**Date:** 2025-02-12
**Project:** 薪日 PayDay - 综合测试覆盖策略

## Overview

本文档定义了薪日项目的综合测试覆盖策略，重点覆盖API端点、服务层集成测试和关键业务流程。

### 当前状态

- ✅ 测试基础设施已就绪（pytest, fixtures）
- ✅ 4个测试文件（基础API、risk_service）
- ❌ 大部分服务未测试（19个服务文件）
- ❌ 大部分API端点未测试（21个API文件）
- ❌ 缺少集成测试和E2E测试

### 测试目标

- **主要目标**: 全面的API覆盖（所有端点的成功/失败路径）
- **服务层测试**: 集成测试（真实数据库事务）
- **CI/CD**: 手动测试模式，暂不配置自动化CI

## 1. 测试架构与组织

### 目录结构

```
backend/tests/
├── conftest.py              # 共享fixtures（已存在）
├── test_utils.py            # 测试辅助函数
├── api/                     # API端点测试
│   ├── __init__.py
│   ├── test_auth.py         # 认证端点
│   ├── test_user.py         # 用户管理
│   ├── test_payday.py       # 薪日配置
│   ├── test_salary.py       # 薪资记录
│   ├── test_post.py         # 社区帖子
│   ├── test_comment.py      # 评论
│   ├── test_like.py         # 点赞
│   ├── test_follow.py       # 关注关系
│   ├── test_notification.py # 通知
│   ├── test_statistics.py   # 统计数据
│   ├── test_theme.py        # 主题管理
│   ├── test_checkin.py      # 打卡功能
│   ├── test_payment.py      # 支付流程
│   ├── test_membership.py   # 会员功能
│   ├── test_admin.py        # 管理后台
│   └── test_admin_config.py # 管理配置
├── services/                # 服务集成测试
│   ├── __init__.py
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_post_service.py
│   ├── test_payment_service.py
│   ├── test_salary_service.py
│   └── ... (每个服务一个文件)
└── tasks/                   # Celery任务测试
    ├── __init__.py
    └── test_risk_check.py
```

### 测试策略

- **API测试**: 使用TestClient + 测试数据库，测试完整请求/响应周期
- **服务测试**: 使用异步测试数据库 + 真实事务，仅模拟外部服务
- **任务测试**: 模拟Celery执行环境

## 2. 测试数据与Fixtures

### 核心Fixtures（conftest.py扩展）

```python
# 认证fixtures
@pytest.fixture
async def test_user(db_session):
    """创建测试用户（微信认证）"""
    user = User(openid="test_openid", nickname="测试用户")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_headers(test_user):
    """生成认证请求头"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

# 数据工厂fixtures
@pytest.fixture
async def test_post(db_session, test_user):
    """创建测试帖子"""
    post = Post(user_id=test_user.id, content="测试内容", mood="happy")
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    return post

@pytest.fixture
async def test_salary(db_session, test_user):
    """创建测试薪资记录（加密）"""
    from app.utils.encryption import encryption_service
    salary = Salary(
        user_id=test_user.id,
        amount_encrypted=encryption_service.encrypt_amount(10000),
        month="2024-01"
    )
    db_session.add(salary)
    await db_session.commit()
    await db_session.refresh(salary)
    return salary

# 外部服务mocks
@pytest.fixture
def mock_wechat_service():
    """Mock微信API调用"""
    with patch('app.services.auth_service.wechat_code2session') as mock:
        mock.return_value = {"openid": "test_openid", "session_key": "test_key"}
        yield mock

@pytest.fixture
def mock_wechat_pay():
    """Mock微信支付API"""
    with patch('app.services.payment_service.wechat_pay') as mock:
        mock.create_order.return_value = {
            "prepay_id": "prepay_test",
            "code_url": "weixin://wxpay/bizpayurl?pr=test"
        }
        mock.query_order.return_value = {
            "trade_state": "SUCCESS",
            "transaction_id": "txn_test_123"
        }
        yield mock

@pytest.fixture
def mock_yu_service():
    """Mock腾讯云天御（内容审核）"""
    with patch('app.services.risk_service.yu_client') as mock:
        mock.text_moderation.return_value = {"Pass": True, "Score": 0}
        mock.image_moderation.return_value = {"Pass": True, "Score": 0}
        yield mock
```

### 测试工具类（test_utils.py）

```python
class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    async def create_user(db_session, **kwargs):
        """创建用户（默认值+自定义覆盖）"""
        defaults = {
            "openid": f"test_{uuid4().hex}",
            "nickname": "测试用户",
            "avatar_url": None
        }
        defaults.update(kwargs)
        user = User(**defaults)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @staticmethod
    async def create_post(db_session, user_id, **kwargs):
        """创建帖子"""
        defaults = {
            "content": "测试内容",
            "mood": "happy",
            "images": []
        }
        defaults.update(kwargs)
        post = Post(user_id=user_id, **defaults)
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        return post
```

## 3. API测试模式

### 标准API测试模板

```python
class TestPostAPI:
    """帖子API测试"""

    @pytest.mark.asyncio
    async def test_create_post_success(self, client, db_session, test_user, auth_headers):
        """测试创建帖子成功"""
        response = client.post(
            "/api/v1/posts/",
            json={"content": "这是测试内容", "mood": "happy"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "这是测试内容"
        assert data["mood"] == "happy"
        assert "id" in data

        # 验证数据库
        stmt = select(Post).where(Post.id == data["id"])
        result = await db_session.execute(stmt)
        post = result.scalar_one()
        assert post is not None

    @pytest.mark.asyncio
    async def test_create_post_unauthorized(self, client):
        """测试未授权创建帖子"""
        response = client.post(
            "/api/v1/posts/",
            json={"content": "这是测试内容"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_post_with_sensitive_content(self, client, auth_headers):
        """测试创建含敏感词帖子"""
        response = client.post(
            "/api/v1/posts/",
            json={"content": "违禁词1 测试", "mood": "happy"},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "敏感词" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_posts_pagination(self, client, db_session, test_user, auth_headers):
        """测试分页获取帖子"""
        # 创建多个帖子
        for i in range(15):
            post = Post(user_id=test_user.id, content=f"测试{i}")
            db_session.add(post)
        await db_session.commit()

        response = client.get("/api/v1/posts/?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
```

### 每个端点的测试类别

- ✅ 成功路径（happy path）
- ❌ 认证/授权失败
- 📝 验证错误（无效输入）
- 🔒 业务逻辑约束（重复、限制）
- 🚫 边界情况（空结果、最大限制）

## 4. 服务集成测试

### 集成测试模式（真实数据库）

```python
class TestPostService:
    """帖子服务集成测试"""

    @pytest.mark.asyncio
    async def test_create_post_with_db(self, db_session):
        """测试创建帖子（真实数据库事务）"""
        # 先创建用户
        user = User(openid="test_openid", nickname="测试")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 调用服务
        from app.services.post_service import create_post
        post = await create_post(
            db_session,
            user_id=user.id,
            content="测试内容",
            mood="happy"
        )

        # 验证数据库
        assert post.id is not None
        assert post.content == "测试内容"

        # 从DB查询验证持久化
        stmt = select(Post).where(Post.id == post.id)
        result = await db_session.execute(stmt)
        saved_post = result.scalar_one()
        assert saved_post.content == "测试内容"

    @pytest.mark.asyncio
    async def test_delete_post_cascade(self, db_session):
        """测试删除帖子级联删除评论"""
        user = User(openid="test_openid")
        post = Post(user_id=user.id, content="测试")
        comment = Comment(post_id=post.id, user_id=user.id, content="评论")
        db_session.add_all([user, post, comment])
        await db_session.commit()

        # 删除帖子
        await post_service.delete_post(db_session, post.id)

        # 验证评论也被删除
        stmt = select(Comment).where(Comment.post_id == post.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
```

### 服务测试类别

- 🗄️ 数据库CRUD操作
- 🔗 关系管理（级联删除、连接查询）
- 💰 事务处理（错误回滚）
- 📊 复杂查询（分页、过滤、排序）

## 5. 外部服务Mock与支付测试

### 外部服务Mock模式

```python
class TestPaymentService:
    """支付服务测试"""

    @pytest.fixture
    def mock_wechat_pay(self):
        """Mock微信支付API"""
        with patch('app.services.payment_service.wechat_pay') as mock:
            mock.create_order.return_value = {
                "prepay_id": "prepay_test",
                "code_url": "weixin://wxpay/bizpayurl?pr=test"
            }
            mock.query_order.return_value = {
                "trade_state": "SUCCESS",
                "transaction_id": "txn_test_123"
            }
            yield mock

    @pytest.mark.asyncio
    async def test_create_payment_order(self, db_session, mock_wechat_pay):
        """测试创建支付订单"""
        user = await TestDataFactory.create_user(db_session)
        membership = await TestDataFactory.create_membership(db_session, price=9900)

        order = await payment_service.create_order(
            db_session,
            user_id=user.id,
            membership_id=membership.id
        )

        assert order.status == OrderStatus.PENDING
        assert order.amount == 9900
        mock_wechat_pay.create_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_success_flow(self, db_session, mock_wechat_pay):
        """测试支付成功流程"""
        # 创建待支付订单
        order = await TestDataFactory.create_order(
            db_session,
            status=OrderStatus.PENDING
        )

        # 模拟支付回调
        await payment_service.handle_payment_callback(
            db_session,
            order_id=order.id,
            transaction_id="txn_test_123"
        )

        # 验证订单已更新
        await db_session.refresh(order)
        assert order.status == OrderStatus.PAID

        # 验证会员已激活
        user_membership = await user_membership_service.get_active(order.user_id)
        assert user_membership is not None
```

### 模拟的外部服务

- 🟢 微信小程序认证（code2session）
- 🟢 微信支付（create_order, query_order, callback）
- 🟢 腾讯云天御（内容审核）
- 🟢 腾讯云COS（图片存储）
- 🟢 Celery任务（用于同步测试）

## 6. 测试配置与覆盖率

### pytest.ini 配置

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    asyncio: Async tests
    integration: Integration tests
    slow: Slow-running tests
    payment: Payment-related tests
addopts =
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=60
```

### 测试命令

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/api/test_post.py

# 仅运行API测试
pytest tests/api/

# 仅运行快速测试（排除慢测试）
pytest -m "not slow"

# 仅运行支付测试
pytest -m payment

# 详细输出
pytest -v -s

# 特定模块覆盖率
pytest --cov=app.services.post_service --cov=app.api.v1.post
```

### 覆盖率目标

| 模块 | 目标覆盖率 | 优先级 |
|------|-----------|--------|
| Payment service | 95% | 关键 |
| Auth service | 90% | 关键 |
| Salary encryption | 95% | 关键 |
| Risk service | 85% | 高 |
| Post/Comment services | 80% | 高 |
| Other services | 70% | 中 |
| API routes | 75% | 中 |
| Models (via usage) | 60% | 低 |

## 7. 实施计划

### 第一阶段 - 关键路径（第1周）

**优先级: 关键**
**重点: 认证、支付、薪资加密**

1. test_auth.py - 登录、token刷新、用户注册
2. test_payment.py - 支付流程、回调处理、订单状态
3. test_salary.py - 薪资CRUD + 加密/解密
4. test_auth_service.py - JWT生成、验证
5. test_payment_service.py - 订单创建、状态更新
6. test_salary_service.py - 加密操作、查询

### 第二阶段 - 核心功能（第2周）

**优先级: 高**
**重点: 帖子、评论、点赞、风控**

1. test_post.py - CRUD、分页、过滤
2. test_comment.py - CRUD、嵌套回复
3. test_like.py - 切换、列表、用户点赞
4. test_risk_check.py - 内容审核任务
5. test_post_service.py - 业务逻辑、缓存
6. test_risk_service.py - （扩展现有测试）

### 第三阶段 - 社交功能（第3周）

**优先级: 中**
**重点: 关注、通知、统计**

1. test_follow.py - 关注/取消、粉丝列表
2. test_notification.py - 列表、标记已读、通知
3. test_statistics.py - 用户统计、平台统计
4. test_follow_service.py - 关系管理
5. test_notification_service.py - 通知生成

### 第四阶段 - 附加功能（第4周）

**优先级: 中低**
**重点: 主题、打卡、管理、配置**

1. test_theme.py - 主题选择、用户主题
2. test_checkin.py - 每日打卡、连续打卡
3. test_admin.py - 管理后台访问、用户管理
4. test_admin_config.py - 会员配置、主题配置
5. test_recommendation.py - 内容推荐

### 每个测试文件的实施步骤

1. 创建测试文件及类结构
2. 添加fixture依赖（user, auth_headers等）
3. 编写成功路径测试
4. 编写失败路径测试（401, 400, 404）
5. 编写边界情况测试
6. 运行并验证覆盖率
7. 记录任何未覆盖的缺口

## 8. 测试最佳实践

### 命名约定

- 测试文件: `test_<module>.py`
- 测试类: `Test<ClassName>`
- 测试函数: `test_<action>_<scenario>_<expected_result>`

### 示例

```python
async def test_create_post_without_auth_returns_401(client):
    """测试: 创建帖子 无认证 返回401"""
    pass

async def test_get_posts_with_pagination_returns_correct_count(client, auth_headers):
    """测试: 获取帖子 带分页 返回正确数量"""
    pass
```

### 测试隔离

- 每个测试独立运行
- 使用`db_session` fixture自动回滚
- 避免测试间依赖

### Mock使用

- 仅mock外部服务（微信API、腾讯云）
- 数据库操作使用真实测试数据库
- 保持mock简单，专注测试目标

## 9. 维护与扩展

### 添加新功能的测试

当添加新功能时：

1. 在相应目录创建测试文件
2. 复用现有fixtures
3. 遵循测试模式
4. 确保覆盖率达标

### 定期检查

- 每次PR前运行: `pytest --cov`
- 查看覆盖率报告: `htmlcov/index.html`
- 更新测试以修复bug

## 10. 总结

本测试策略提供：

- ✅ 全面的API覆盖（所有端点）
- ✅ 服务层集成测试（真实数据库）
- ✅ 关键业务流程保护（支付、加密）
- ✅ 可维护的测试结构
- ✅ 清晰的实施计划

预期成果：
- 整体代码覆盖率: 75%+
- 关键模块覆盖率: 90%+
- 可靠的回归测试套件
