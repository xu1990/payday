# Comprehensive Test Coverage - Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build comprehensive test coverage for critical backend paths (auth, payment, salary) with integration tests using real database transactions.

**Architecture:**
- Test structure: `tests/api/` for endpoint tests, `tests/services/` for service integration tests
- Fixtures in `conftest.py` for reusable test data (users, auth headers, posts)
- Real database with in-memory SQLite for fast, isolated tests
- Mock only external services (WeChat, Tencent Cloud, payment gateways)

**Tech Stack:**
- pytest + pytest-asyncio for async testing
- SQLAlchemy async sessions for database integration
- TestClient for FastAPI endpoint testing
- unittest.mock for external service mocking

---

## Prerequisites Setup

### Task 0: Test Infrastructure Enhancement

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_utils.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/services/__init__.py`

**Step 1: Create test_utils.py with data factory**

```python
"""测试工具和数据工厂"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.post import Post
from app.models.salary import Salary
from app.models.membership import Membership, UserMembership
from app.models.order import Order
from app.models.notification import Notification
from app.utils.encryption import encryption_service


class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    async def create_user(
        db_session: AsyncSession,
        openid: str = None,
        nickname: str = "测试用户",
        **kwargs
    ) -> User:
        """创建测试用户"""
        if openid is None:
            openid = f"test_{uuid.uuid4().hex[:16]}"

        user = User(
            openid=openid,
            nickname=nickname,
            avatar_url=kwargs.get("avatar_url"),
            bio=kwargs.get("bio"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @staticmethod
    async def create_post(
        db_session: AsyncSession,
        user_id: int,
        content: str = "测试内容",
        mood: str = "happy",
        **kwargs
    ) -> Post:
        """创建测试帖子"""
        post = Post(
            user_id=user_id,
            content=content,
            mood=mood,
            images=kwargs.get("images", []),
            is_anonymous=kwargs.get("is_anonymous", False),
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        return post

    @staticmethod
    async def create_salary(
        db_session: AsyncSession,
        user_id: int,
        amount: int = 10000,
        month: str = "2024-01",
        **kwargs
    ) -> Salary:
        """创建测试薪资记录"""
        salary = Salary(
            user_id=user_id,
            amount_encrypted=encryption_service.encrypt_amount(amount),
            month=month,
            company=kwargs.get("company"),
            position=kwargs.get("position"),
            city=kwargs.get("city"),
        )
        db_session.add(salary)
        await db_session.commit()
        await db_session.refresh(salary)
        return salary

    @staticmethod
    async def create_membership(
        db_session: AsyncSession,
        name: str = "月度会员",
        price: int = 9900,
        duration_days: int = 30,
        **kwargs
    ) -> Membership:
        """创建测试会员套餐"""
        membership = Membership(
            name=name,
            price=price,
            duration_days=duration_days,
            features=kwargs.get("features", []),
            is_active=kwargs.get("is_active", True),
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)
        return membership

    @staticmethod
    async def create_order(
        db_session: AsyncSession,
        user_id: int,
        membership_id: int = None,
        amount: int = 9900,
        status: str = "pending",
        **kwargs
    ) -> Order:
        """创建测试订单"""
        order = Order(
            user_id=user_id,
            membership_id=membership_id,
            amount=amount,
            status=status,
            transaction_id=kwargs.get("transaction_id"),
            prepay_id=kwargs.get("prepay_id"),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        return order

    @staticmethod
    async def create_notification(
        db_session: AsyncSession,
        user_id: int,
        type: str = "system",
        title: str = "测试通知",
        content: str = "这是测试内容",
        **kwargs
    ) -> Notification:
        """创建测试通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            related_type=kwargs.get("related_type"),
            related_id=kwargs.get("related_id"),
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        return notification
```

Run: No command needed
Expected: File created

**Step 2: Update conftest.py with additional fixtures**

Add to `backend/tests/conftest.py`:

```python
# Import models and factory
from app.models.user import User
from app.models.post import Post
from app.models.salary import Salary
from app.models.membership import Membership, UserMembership
from app.models.order import Order
from app.core.security import create_access_token
from tests.test_utils import TestDataFactory


# Fixtures for authenticated requests
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    return await TestDataFactory.create_user(db_session)


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        openid="admin_test",
        nickname="测试管理员",
        is_admin=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(test_user: User) -> str:
    """生成用户JWT token"""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """生成管理员JWT token"""
    return create_access_token(
        data={"sub": str(test_admin.id), "scope": "admin"}
    )


@pytest.fixture
def user_headers(user_token: str) -> dict:
    """用户认证请求头"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """管理员认证请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


# External service mock fixtures
@pytest.fixture
def mock_wechat_auth():
    """Mock微信认证API"""
    with patch('app.services.auth_service.wechat_code2session', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "openid": "test_openid",
            "session_key": "test_session_key"
        }
        yield mock


@pytest.fixture
def mock_wechat_pay():
    """Mock微信支付API"""
    with patch('app.services.payment_service.wechat_pay') as mock:
        mock.create_order = AsyncMock(return_value={
            "prepay_id": "prepay_id_test_123",
            "code_url": "weixin://wxpay/bizpayurl?pr=test"
        })
        mock.query_order = AsyncMock(return_value={
            "trade_state": "SUCCESS",
            "transaction_id": "txn_test_123"
        })
        mock.close_order = AsyncMock(return_value={})
        yield mock


@pytest.fixture
def mock_yu_moderation():
    """Mock腾讯云天御内容审核"""
    with patch('app.services.risk_service.yu_client') as mock:
        mock.text_moderation = AsyncMock(return_value={
            "Pass": True,
            "Score": 0,
            "Label": ""
        })
        mock.image_moderation = AsyncMock(return_value={
            "Pass": True,
            "Score": 0,
            "Label": ""
        })
        yield mock


@pytest.fixture
def mock_cos_upload():
    """Mock腾讯云COS上传"""
    with patch('app.services.storage_service.cos_client') as mock:
        mock.upload_file = AsyncMock(return_value={
            "url": "https://test.cos.ap-guangzhou.myqcloud.com/test.jpg",
            "path": "test.jpg"
        })
        yield mock


# Data fixtures
@pytest.fixture
async def test_post(db_session: AsyncSession, test_user: User) -> Post:
    """创建测试帖子"""
    return await TestDataFactory.create_post(db_session, test_user.id)


@pytest.fixture
async def test_salary(db_session: AsyncSession, test_user: User) -> Salary:
    """创建测试薪资记录"""
    return await TestDataFactory.create_salary(db_session, test_user.id)


@pytest.fixture
async def test_membership(db_session: AsyncSession) -> Membership:
    """创建测试会员套餐"""
    return await TestDataFactory.create_membership(db_session)


@pytest.fixture
async def test_order(
    db_session: AsyncSession,
    test_user: User,
    test_membership: Membership
) -> Order:
    """创建测试订单"""
    return await TestDataFactory.create_order(
        db_session,
        test_user.id,
        test_membership.id
    )
```

Run: `cd backend && python -c "from tests.conftest import *; print('Fixtures loaded successfully')"`
Expected: No errors

**Step 3: Create api and services test directories**

```bash
mkdir -p backend/tests/api
mkdir -p backend/tests/services
touch backend/tests/api/__init__.py
touch backend/tests/services/__init__.py
```

Run: `ls -la backend/tests/api/ backend/tests/services/`
Expected: Directories created with __init__.py files

**Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_utils.py backend/tests/api/__init__.py backend/tests/services/__init__.py
git commit -m "test: enhance test infrastructure with data factory and fixtures"
```

---

## Phase 1.1: Authentication Tests

### Task 1: Auth Service Integration Tests

**Files:**
- Create: `backend/tests/services/test_auth_service.py`

**Step 1: Write auth service tests**

```python
"""认证服务集成测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.auth_service import (
    get_or_create_user_by_code,
    refresh_user_token,
)
from app.models.user import User
from tests.test_utils import TestDataFactory


class TestGetOrCreateUserByCode:
    """测试通过微信code获取或创建用户"""

    @pytest.mark.asyncio
    async def test_new_user_creation(self, db_session: AsyncSession, mock_wechat_auth):
        """测试新用户创建"""
        # Mock返回新的openid
        mock_wechat_auth.return_value = {
            "openid": "new_user_openid",
            "session_key": "session_key"
        }

        user = await get_or_create_user_by_code(
            db_session,
            code="test_code"
        )

        assert user.id is not None
        assert user.openid == "new_user_openid"
        mock_wechat_auth.assert_called_once()

    @pytest.mark.asyncio
    async def test_existing_user_login(self, db_session: AsyncSession, mock_wechat_auth):
        """测试已存在用户登录"""
        # 先创建用户
        existing_user = await TestDataFactory.create_user(
            db_session,
            openid="existing_openid"
        )

        # Mock返回已存在的openid
        mock_wechat_auth.return_value = {
            "openid": "existing_openid",
            "session_key": "new_session_key"
        }

        user = await get_or_create_user_by_code(
            db_session,
            code="test_code"
        )

        assert user.id == existing_user.id
        assert user.openid == "existing_openid"

    @pytest.mark.asyncio
    async def test_invalid_code_raises_error(self, db_session: AsyncSession, mock_wechat_auth):
        """测试无效code抛出错误"""
        # Mock微信API返回错误
        mock_wechat_auth.side_effect = Exception("Invalid code")

        with pytest.raises(Exception, match="Invalid code"):
            await get_or_create_user_by_code(
                db_session,
                code="invalid_code"
            )


class TestRefreshUserToken:
    """测试刷新用户token"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, db_session: AsyncSession):
        """测试刷新token成功"""
        user = await TestDataFactory.create_user(db_session)

        token_data = await refresh_user_token(
            db_session,
            user_id=user.id
        )

        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert "expires_in" in token_data

    @pytest.mark.asyncio
    async def test_refresh_token_nonexistent_user(self, db_session: AsyncSession):
        """测试不存在的用户刷新token"""
        with pytest.raises(Exception):  # Should raise NotFoundException
            await refresh_user_token(
                db_session,
                user_id=99999
            )
```

Run: `cd backend && pytest tests/services/test_auth_service.py -v`
Expected: Tests fail (service methods need to be checked/implemented)

**Step 2: Run tests to verify auth service exists**

Run: `cd backend && pytest tests/services/test_auth_service.py -v`
Expected: Either tests pass if methods exist, or clear error messages if methods need to be adjusted

**Step 3: Adjust tests based on actual auth_service implementation**

Read `backend/app/services/auth_service.py` and adjust test expectations accordingly.

**Step 4: Run tests again**

Run: `cd backend && pytest tests/services/test_auth_service.py -v`
Expected: Tests pass

**Step 5: Commit**

```bash
git add backend/tests/services/test_auth_service.py
git commit -m "test: add auth service integration tests"
```

---

### Task 2: Auth API Endpoint Tests

**Files:**
- Create: `backend/tests/api/test_auth.py`

**Step 1: Write auth API tests**

```python
"""认证API端点测试"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestLoginEndpoint:
    """测试登录端点"""

    def test_login_success(self, client: TestClient, mock_wechat_auth):
        """测试登录成功"""
        mock_wechat_auth.return_value = {
            "openid": "test_openid",
            "session_key": "test_key"
        }

        response = client.post(
            "/api/v1/auth/login",
            json={"code": "test_code"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_missing_code(self, client: TestClient):
        """测试缺少code参数"""
        response = client.post(
            "/api/v1/auth/login",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_login_invalid_code(self, client: TestClient, mock_wechat_auth):
        """测试无效code"""
        mock_wechat_auth.side_effect = Exception("Invalid code")

        response = client.post(
            "/api/v1/auth/login",
            json={"code": "invalid_code"}
        )

        assert response.status_code == 400


class TestRefreshTokenEndpoint:
    """测试刷新token端点"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        client: TestClient,
        test_user,
        user_headers
    ):
        """测试刷新token成功"""
        response = client.post(
            "/api/v1/auth/refresh",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_unauthorized(self, client: TestClient):
        """测试未授权刷新token"""
        response = client.post(
            "/api/v1/auth/refresh"
        )

        assert response.status_code == 401


class TestGetUserProfile:
    """测试获取用户信息端点"""

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self,
        client: TestClient,
        test_user,
        user_headers
    ):
        """测试获取用户信息成功"""
        response = client.get(
            "/api/v1/auth/me",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["nickname"] == test_user.nickname

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: TestClient):
        """测试未授权获取用户信息"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
```

Run: `cd backend && pytest tests/api/test_auth.py -v`
Expected: Tests fail (need to check API implementation)

**Step 2: Check actual auth API endpoints**

Read `backend/app/api/v1/auth.py` to verify endpoint paths and behavior.

**Step 3: Adjust tests based on actual implementation**

Update test assertions and expected responses based on actual API behavior.

**Step 4: Run tests again**

Run: `cd backend && pytest tests/api/test_auth.py -v`
Expected: Tests pass

**Step 5: Commit**

```bash
git add backend/tests/api/test_auth.py
git commit -m "test: add auth API endpoint tests"
```

---

## Phase 1.2: Payment Tests

### Task 3: Payment Service Integration Tests

**Files:**
- Create: `backend/tests/services/test_payment_service.py`

**Step 1: Write payment service tests**

```python
"""支付服务集成测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.payment_service import (
    create_order,
    handle_payment_callback,
    get_order_status,
)
from app.models.order import Order, OrderStatus
from tests.test_utils import TestDataFactory


class TestCreateOrder:
    """测试创建支付订单"""

    @pytest.mark.asyncio
    async def test_create_order_success(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
        mock_wechat_pay
    ):
        """测试创建订单成功"""
        order = await create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id
        )

        assert order.id is not None
        assert order.user_id == test_user.id
        assert order.membership_id == test_membership.id
        assert order.status == OrderStatus.PENDING
        assert order.amount == test_membership.price
        assert order.prepay_id is not None

    @pytest.mark.asyncio
    async def test_create_order_with_invalid_membership(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """测试创建订单时会员套餐不存在"""
        with pytest.raises(Exception):  # Should raise NotFoundException
            await create_order(
                db_session,
                user_id=test_user.id,
                membership_id=99999
            )


class TestHandlePaymentCallback:
    """测试处理支付回调"""

    @pytest.mark.asyncio
    async def test_payment_success_callback(
        self,
        db_session: AsyncSession,
        test_order,
        test_membership,
        mock_wechat_pay
    ):
        """测试支付成功回调"""
        result = await handle_payment_callback(
            db_session,
            order_id=test_order.id,
            transaction_id="txn_test_123",
            total_fee=test_order.amount
        )

        await db_session.refresh(test_order)
        assert test_order.status == OrderStatus.PAID
        assert test_order.transaction_id == "txn_test_123"

    @pytest.mark.asyncio
    async def test_payment_callback_order_not_exist(self, db_session: AsyncSession):
        """测试回调时订单不存在"""
        with pytest.raises(Exception):
            await handle_payment_callback(
                db_session,
                order_id=99999,
                transaction_id="txn_test",
                total_fee=100
            )


class TestGetOrderStatus:
    """测试获取订单状态"""

    @pytest.mark.asyncio
    async def test_get_order_status_success(
        self,
        db_session: AsyncSession,
        test_order
    ):
        """测试获取订单状态成功"""
        status = await get_order_status(
            db_session,
            order_id=test_order.id
        )

        assert status["order_id"] == test_order.id
        assert status["status"] == test_order.status
        assert status["amount"] == test_order.amount

    @pytest.mark.asyncio
    async def test_get_order_status_not_found(self, db_session: AsyncSession):
        """测试获取不存在的订单状态"""
        with pytest.raises(Exception):
            await get_order_status(
                db_session,
                order_id=99999
            )
```

Run: `cd backend && pytest tests/services/test_payment_service.py -v`
Expected: Tests fail or pass depending on implementation

**Step 2: Check payment service implementation**

Read `backend/app/services/payment_service.py` and adjust tests accordingly.

**Step 3: Run tests again**

Run: `cd backend && pytest tests/services/test_payment_service.py -v`
Expected: Tests pass after adjustments

**Step 4: Commit**

```bash
git add backend/tests/services/test_payment_service.py
git commit -m "test: add payment service integration tests"
```

---

### Task 4: Payment API Endpoint Tests

**Files:**
- Create: `backend/tests/api/test_payment.py`

**Step 1: Write payment API tests**

```python
"""支付API端点测试"""
import pytest
from fastapi.testclient import TestClient


class TestCreatePaymentOrder:
    """测试创建支付订单"""

    @pytest.mark.asyncio
    async def test_create_order_success(
        self,
        client: TestClient,
        test_user,
        test_membership,
        user_headers,
        mock_wechat_pay
    ):
        """测试创建订单成功"""
        response = client.post(
            "/api/v1/payment/orders",
            json={"membership_id": test_membership.id},
            headers=user_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["amount"] == test_membership.price
        assert data["prepay_id"] is not None

    @pytest.mark.asyncio
    async def test_create_order_unauthorized(
        self,
        client: TestClient,
        test_membership
    ):
        """测试未授权创建订单"""
        response = client.post(
            "/api/v1/payment/orders",
            json={"membership_id": test_membership.id}
        )

        assert response.status_code == 401


class TestPaymentCallback:
    """测试支付回调端点"""

    @pytest.mark.asyncio
    async def test_payment_callback_success(
        self,
        client: TestClient,
        test_order,
        mock_wechat_pay
    ):
        """测试支付回调成功"""
        callback_data = {
            "order_id": test_order.id,
            "transaction_id": "txn_test_123",
            "total_fee": test_order.amount
        }

        response = client.post(
            "/api/v1/payment/callback",
            json=callback_data
        )

        assert response.status_code == 200


class TestGetOrderStatus:
    """测试查询订单状态"""

    @pytest.mark.asyncio
    async def test_get_order_status_success(
        self,
        client: TestClient,
        test_order,
        user_headers
    ):
        """测试查询订单状态成功"""
        response = client.get(
            f"/api/v1/payment/orders/{test_order.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id
        assert "status" in data

    @pytest.mark.asyncio
    async def test_get_order_status_unauthorized(
        self,
        client: TestClient,
        test_order
    ):
        """测试未授权查询订单"""
        response = client.get(f"/api/v1/payment/orders/{test_order.id}")

        assert response.status_code == 401
```

Run: `cd backend && pytest tests/api/test_payment.py -v`
Expected: Tests fail or pass based on implementation

**Step 2: Check payment API implementation**

Read `backend/app/api/v1/payment.py` and adjust tests.

**Step 3: Run tests again**

Run: `cd backend && pytest tests/api/test_payment.py -v`
Expected: Tests pass

**Step 4: Commit**

```bash
git add backend/tests/api/test_payment.py
git commit -m "test: add payment API endpoint tests"
```

---

## Phase 1.3: Salary Tests

### Task 5: Salary Service Integration Tests

**Files:**
- Create: `backend/tests/services/test_salary_service.py`

**Step 1: Write salary service tests**

```python
"""薪资服务集成测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.salary_service import (
    create_salary,
    get_user_salaries,
    get_salary_by_id,
    update_salary,
    delete_salary,
)
from app.models.salary import Salary
from app.utils.encryption import encryption_service
from tests.test_utils import TestDataFactory


class TestCreateSalary:
    """测试创建薪资记录"""

    @pytest.mark.asyncio
    async def test_create_salary_success(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """测试创建薪资记录成功"""
        salary = await create_salary(
            db_session,
            user_id=test_user.id,
            amount=15000,
            month="2024-01",
            company="测试公司",
            position="工程师",
            city="深圳"
        )

        assert salary.id is not None
        assert salary.user_id == test_user.id

        # 验证加密存储
        decrypted_amount = encryption_service.decrypt_amount(
            salary.amount_encrypted
        )
        assert decrypted_amount == 15000

    @pytest.mark.asyncio
    async def test_create_salary_duplicate_month(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """测试同月重复创建"""
        # 创建第一条记录
        await create_salary(
            db_session,
            user_id=test_user.id,
            amount=10000,
            month="2024-01"
        )

        # 尝试创建同月第二条记录
        with pytest.raises(Exception):  # Should raise BusinessException
            await create_salary(
                db_session,
                user_id=test_user.id,
                amount=12000,
                month="2024-01"
            )


class TestGetUserSalaries:
    """测试获取用户薪资列表"""

    @pytest.mark.asyncio
    async def test_get_salaries_with_pagination(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """测试分页获取薪资"""
        # 创建多条记录
        for i in range(5):
            await TestDataFactory.create_salary(
                db_session,
                user_id=test_user.id,
                month=f"2024-{i+1:02d}"
            )

        salaries, total = await get_user_salaries(
            db_session,
            user_id=test_user.id,
            page=1,
            page_size=3
        )

        assert len(salaries) == 3
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_salaries_empty(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """测试获取空列表"""
        salaries, total = await get_user_salaries(
            db_session,
            user_id=test_user.id
        )

        assert len(salaries) == 0
        assert total == 0


class TestUpdateSalary:
    """测试更新薪资记录"""

    @pytest.mark.asyncio
    async def test_update_salary_success(
        self,
        db_session: AsyncSession,
        test_salary
    ):
        """测试更新薪资成功"""
        updated_salary = await update_salary(
            db_session,
            salary_id=test_salary.id,
            user_id=test_salary.user_id,
            amount=20000,
            company="新公司"
        )

        decrypted_amount = encryption_service.decrypt_amount(
            updated_salary.amount_encrypted
        )
        assert decrypted_amount == 20000
        assert updated_salary.company == "新公司"

    @pytest.mark.asyncio
    async def test_update_salary_unauthorized_user(
        self,
        db_session: AsyncSession,
        test_salary
    ):
        """测试未授权用户更新"""
        other_user = await TestDataFactory.create_user(db_session)

        with pytest.raises(Exception):  # Should raise ForbiddenException
            await update_salary(
                db_session,
                salary_id=test_salary.id,
                user_id=other_user.id,
                amount=20000
            )
```

Run: `cd backend && pytest tests/services/test_salary_service.py -v`
Expected: Tests fail or pass

**Step 2: Check salary service implementation**

Read `backend/app/services/salary_service.py` and adjust.

**Step 3: Run tests again**

Run: `cd backend && pytest tests/services/test_salary_service.py -v`
Expected: Tests pass

**Step 4: Commit**

```bash
git add backend/tests/services/test_salary_service.py
git commit -m "test: add salary service integration tests"
```

---

### Task 6: Salary API Endpoint Tests

**Files:**
- Create: `backend/tests/api/test_salary.py`

**Step 1: Write salary API tests**

```python
"""薪资API端点测试"""
import pytest
from fastapi.testclient import TestClient


class TestCreateSalary:
    """测试创建薪资记录"""

    @pytest.mark.asyncio
    async def test_create_salary_success(
        self,
        client: TestClient,
        test_user,
        user_headers
    ):
        """测试创建薪资成功"""
        response = client.post(
            "/api/v1/salary/",
            json={
                "amount": 15000,
                "month": "2024-01",
                "company": "测试公司",
                "position": "工程师",
                "city": "深圳"
            },
            headers=user_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        # 注意: 响应中可能返回加密金额或脱敏金额

    @pytest.mark.asyncio
    async def test_create_salary_unauthorized(
        self,
        client: TestClient
    ):
        """测试未授权创建"""
        response = client.post(
            "/api/v1/salary/",
            json={"amount": 15000, "month": "2024-01"}
        )

        assert response.status_code == 401


class TestGetSalaries:
    """测试获取薪资列表"""

    @pytest.mark.asyncio
    async def test_get_salaries_with_pagination(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_headers
    ):
        """测试分页获取"""
        # 创建多条记录
        for i in range(5):
            await TestDataFactory.create_salary(
                db_session,
                test_user.id,
                month=f"2024-{i+1:02d}"
            )

        response = client.get(
            "/api/v1/salary/?page=1&page_size=3",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5


class TestGetSalaryDetail:
    """测试获取薪资详情"""

    @pytest.mark.asyncio
    async def test_get_salary_success(
        self,
        client: TestClient,
        test_salary,
        user_headers
    ):
        """测试获取详情成功"""
        response = client.get(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_salary.id

    @pytest.mark.asyncio
    async def test_get_salary_unauthorized_user(
        self,
        client: TestClient,
        db_session,
        test_salary
    ):
        """测试获取其他用户薪资"""
        other_user = await TestDataFactory.create_user(db_session)
        token = create_access_token(data={"sub": str(other_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"/api/v1/salary/{test_salary.id}",
            headers=headers
        )

        assert response.status_code == 403


class TestUpdateSalary:
    """测试更新薪资"""

    @pytest.mark.asyncio
    async def test_update_salary_success(
        self,
        client: TestClient,
        test_salary,
        user_headers
    ):
        """测试更新成功"""
        response = client.put(
            f"/api/v1/salary/{test_salary.id}",
            json={"amount": 20000, "company": "新公司"},
            headers=user_headers
        )

        assert response.status_code == 200


class TestDeleteSalary:
    """测试删除薪资"""

    @pytest.mark.asyncio
    async def test_delete_salary_success(
        self,
        client: TestClient,
        test_salary,
        user_headers
    ):
        """测试删除成功"""
        response = client.delete(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers
        )

        assert response.status_code == 204
```

Run: `cd backend && pytest tests/api/test_salary.py -v`
Expected: Tests fail or pass

**Step 2: Check salary API implementation**

Read `backend/app/api/v1/salary.py` and adjust.

**Step 3: Run tests again**

Run: `cd backend && pytest tests/api/test_salary.py -v`
Expected: Tests pass

**Step 4: Commit**

```bash
git add backend/tests/api/test_salary.py
git commit -m "test: add salary API endpoint tests"
```

---

## Final Task: Verify Coverage

### Task 7: Coverage Check

**Step 1: Run full test suite with coverage**

```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term-missing
```

Expected: Coverage report generated

**Step 2: Review coverage report**

Open `backend/htmlcov/index.html` in browser

Verify:
- `app/services/auth_service.py`: >80%
- `app/services/payment_service.py`: >85%
- `app/services/salary_service.py`: >85%
- `app/api/v1/auth.py`: >75%
- `app/api/v1/payment.py`: >75%
- `app/api/v1/salary.py`: >75%

**Step 3: Create pytest.ini if not exists**

Create `backend/pytest.ini`:

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
```

**Step 4: Final test run**

```bash
cd backend
pytest
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add backend/pytest.ini
git commit -m "test: add pytest configuration for coverage reporting"
```

---

## Summary

This plan implements comprehensive test coverage for critical paths:

1. ✅ Test infrastructure (fixtures, data factory)
2. ✅ Auth service and API tests
3. ✅ Payment service and API tests
4. ✅ Salary service and API tests
5. ✅ Coverage verification

**Expected results after completion:**
- ~15-20 test files created
- 80%+ coverage on critical modules
- All Phase 1 critical paths tested
- Foundation for Phase 2-4 expansion
