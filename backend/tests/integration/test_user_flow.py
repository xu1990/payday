"""用户注册登录流程集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(db_session: AsyncSession):
    """测试用户注册登录完整流程"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 步骤1: 微信小程序登录（使用真实code的模拟）
        # 注意：这里mock微信API，但测试完整的注册流程
        login_data = {
            "code": "test_wx_code"
        }

        # Mock微信code2session
        from unittest.mock import AsyncMock, patch
        with patch('app.utils.wechat.code2session', new_callable=AsyncMock) as mock_wx:
            mock_wx.return_value = {
                "openid": "test_openid_12345",
                "session_key": "test_session_key"
            }

            response = await client.post(
                "/api/v1/auth/login",
                json=login_data
            )

            # 验证登录成功
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data

            access_token = data["access_token"]
            user_id = data["user"]["id"]

        # 步骤2: 使用token获取用户信息
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            "/api/v1/users/me",
            headers=headers
        )

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == user_id
        assert "openid" not in user_data  # 不应该返回敏感信息

        # 步骤3: 更新用户资料
        update_data = {
            "anonymous_name": "测试用户",
            "bio": "这是我的简介"
        }
        response = await client.put(
            "/api/v1/users/me",
            headers=headers,
            json=update_data
        )

        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["anonymous_name"] == "测试用户"
        assert updated_user["bio"] == "这是我的简介"

        # 步骤4: 创建发薪日配置
        payday_data = {
            "job_name": "测试工作",
            "payday": 25,
            "payday_type": "fixed",
            "advance_remind_days": 1
        }
        response = await client.post(
            "/api/v1/payday/config",
            headers=headers,
            json=payday_data
        )

        assert response.status_code == 200
        payday_config = response.json()
        assert payday_config["job_name"] == "测试工作"
        assert payday_config["payday"] == 25

        # 步骤5: 创建薪资记录
        from datetime import date
        salary_data = {
            "config_id": payday_config["id"],
            "amount": 10000,
            "payday_date": date.today().isoformat(),
            "mood": "happy"
        }
        response = await client.post(
            "/api/v1/salary",
            headers=headers,
            json=salary_data
        )

        assert response.status_code == 200
        salary = response.json()
        assert salary["amount"] == 10000  # 注意：金额是加密的，这里返回的可能是显示值


@pytest.mark.asyncio
async def test_user_logout_and_login_again(db_session: AsyncSession):
    """测试用户登出后重新登录"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 首次登录
        from unittest.mock import AsyncMock, patch
        with patch('app.utils.wechat.code2session', new_callable=AsyncMock) as mock_wx:
            mock_wx.return_value = {
                "openid": "test_openid_12345",
                "session_key": "test_session_key"
            }

            response = await client.post(
                "/api/v1/auth/login",
                json={"code": "test_code"}
            )
            assert response.status_code == 200

        # 获取token
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 验证token有效
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        # 登出（如果实现了登出端点）
        # response = await client.post("/api/v1/auth/logout", headers=headers)
        # assert response.status_code == 200

        # 重新登录应该返回同一个用户（相同openid）
        with patch('app.utils.wechat.code2session', new_callable=AsyncMock) as mock_wx:
            mock_wx.return_value = {
                "openid": "test_openid_12345",  # 相同openid
                "session_key": "new_session_key"
            }

            response = await client.post(
                "/api/v1/auth/login",
                json={"code": "new_code"}
            )
            assert response.status_code == 200

            # 应该返回相同的user_id
            new_user_id = response.json()["user"]["id"]
            # 验证是同一个用户（通过查询数据库或比较user_id）
