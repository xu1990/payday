"""管理端认证服务测试"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_auth_service import (
    get_admin_by_username,
    login_admin,
)
from app.models.admin import AdminUser
from app.core.security import hash_password
from tests.test_utils import TestDataFactory


class MockCsrfManager:
    """Mock CSRF manager for testing"""

    def __init__(self):
        self.tokens = {}

    async def generate_token(self):
        """生成假的CSRF token"""
        import uuid
        return f"csrf_{uuid.uuid4().hex}"

    async def save_token(self, token: str, user_id: str):
        """保存token"""
        self.tokens[token] = user_id


class TestGetAdminByUsername:
    """测试根据用户名获取管理员"""

    @pytest.mark.asyncio
    async def test_get_existing_admin(self, db_session: AsyncSession):
        """测试获取已存在的管理员"""
        # 创建管理员
        admin = AdminUser(
            username="test_admin",
            password_hash=hash_password("test_password"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 查询管理员
        found_admin = await get_admin_by_username(db_session, "test_admin")

        assert found_admin is not None
        assert found_admin.id == admin.id
        assert found_admin.username == "test_admin"

    @pytest.mark.asyncio
    async def test_get_nonexistent_admin(self, db_session: AsyncSession):
        """测试获取不存在的管理员返回None"""
        admin = await get_admin_by_username(db_session, "nonexistent_admin")

        assert admin is None


class TestLoginAdmin:
    """测试管理员登录"""

    @pytest.mark.asyncio
    async def test_login_success(self, db_session: AsyncSession):
        """测试登录成功"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("correct_password"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Mock CSRF manager
        mock_csrf = MockCsrfManager()
        with patch('app.services.admin_auth_service.csrf_manager', mock_csrf):
            result = await login_admin(db_session, "admin_user", "correct_password")

        assert result is not None
        jwt_token, csrf_token = result
        assert jwt_token is not None
        assert csrf_token is not None
        assert csrf_token.startswith("csrf_")
        assert csrf_token in mock_csrf.tokens
        assert mock_csrf.tokens[csrf_token] == str(admin.id)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session: AsyncSession):
        """测试密码错误返回None"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("correct_password"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        # 使用错误密码登录
        result = await login_admin(db_session, "admin_user", "wrong_password")

        assert result is None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, db_session: AsyncSession):
        """测试不存在的用户名返回None"""
        result = await login_admin(db_session, "nonexistent", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_login_jwt_contains_admin_scope(self, db_session: AsyncSession):
        """测试JWT包含admin scope"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("password123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Mock CSRF manager
        mock_csrf = MockCsrfManager()
        with patch('app.services.admin_auth_service.csrf_manager', mock_csrf):
            result = await login_admin(db_session, "admin_user", "password123")

        assert result is not None
        jwt_token, _ = result

        # 验证JWT包含正确的scope (通过解码JWT)
        from app.core.security import decode_token
        payload = decode_token(jwt_token)
        assert payload["scope"] == "admin"
        assert payload["sub"] == str(admin.id)

    @pytest.mark.asyncio
    async def test_login_csrf_token_generated(self, db_session: AsyncSession):
        """测试CSRF token正确生成和保存"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("password123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        # Mock CSRF manager
        mock_csrf = MockCsrfManager()
        with patch('app.services.admin_auth_service.csrf_manager', mock_csrf):
            result = await login_admin(db_session, "admin_user", "password123")

        assert result is not None
        _, csrf_token = result

        # 验证CSRF token已保存
        assert csrf_token in mock_csrf.tokens
        # 验证CSRF token关联了正确的用户ID
        assert mock_csrf.tokens[csrf_token] == str(admin.id)

    @pytest.mark.asyncio
    async def test_login_empty_password(self, db_session: AsyncSession):
        """测试空密码登录失败"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("password123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        # 使用空密码登录
        result = await login_admin(db_session, "admin_user", "")

        assert result is None

    @pytest.mark.asyncio
    async def test_login_empty_username(self, db_session: AsyncSession):
        """测试空用户名登录失败"""
        result = await login_admin(db_session, "", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_login_none_password(self, db_session: AsyncSession):
        """测试None密码登录失败"""
        # 创建管理员
        admin = AdminUser(
            username="admin_user",
            password_hash=hash_password("password123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        # 使用None密码登录
        result = await login_admin(db_session, "admin_user", None)

        assert result is None
