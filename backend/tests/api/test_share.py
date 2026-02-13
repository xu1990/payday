"""分享API测试"""
import pytest
from fastapi import status

from app.models.user import User
from app.models.share import Share
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateShareEndpoint:
    """测试创建分享记录接口"""

    def test_create_share_success(self, client, test_user: User, user_headers: dict):
        """测试成功创建分享记录"""
        response = client.post(
            "/api/v1/share",
            json={
                "target_type": "post",
                "target_id": "post_123",
                "share_channel": "wechat_friend",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["target_type"] == "post"
        assert data["target_id"] == "post_123"
        assert data["share_channel"] == "wechat_friend"
        assert data["share_status"] == "pending"

    def test_create_share_without_auth(self, client):
        """测试未认证用户创建分享记录"""
        response = client.post(
            "/api/v1/share",
            json={
                "target_type": "post",
                "target_id": "post_123",
                "share_channel": "wechat_friend",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_share_to_moments(self, client, test_user: User, user_headers: dict):
        """测试分享到朋友圈"""
        response = client.post(
            "/api/v1/share",
            json={
                "target_type": "salary",
                "target_id": "salary_456",
                "share_channel": "wechat_moments",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["share_channel"] == "wechat_moments"

    def test_create_share_different_target_types(self, client, test_user: User, user_headers: dict):
        """测试创建不同类型的分享记录"""
        target_types = ["post", "salary", "poster"]

        for target_type in target_types:
            response = client.post(
                "/api/v1/share",
                json={
                    "target_type": target_type,
                    "target_id": f"{target_type}_123",
                    "share_channel": "wechat_friend",
                },
                headers=user_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["target_type"] == target_type

    def test_create_share_missing_fields(self, client, test_user: User, user_headers: dict):
        """测试缺少必填字段"""
        # 缺少 target_type
        response = client.post(
            "/api/v1/share",
            json={
                "target_id": "post_123",
                "share_channel": "wechat_friend",
            },
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 缺少 share_channel
        response = client.post(
            "/api/v1/share",
            json={
                "target_type": "post",
                "target_id": "post_123",
            },
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestListSharesEndpoint:
    """测试获取分享记录列表接口"""

    async def test_list_shares_success(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试成功获取分享记录列表"""
        from app.services.share_service import create_share

        # 创建测试数据
        await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await create_share(
            db_session,
            user_id=test_user.id,
            target_type="salary",
            target_id="salary_1",
            share_channel="wechat_moments",
        )

        response = client.get("/api/v1/share", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_shares_with_filter(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试按类型筛选"""
        from app.services.share_service import create_share

        await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await create_share(
            db_session,
            user_id=test_user.id,
            target_type="salary",
            target_id="salary_1",
            share_channel="wechat_moments",
        )

        # 只获取 post 类型
        response = client.get(
            "/api/v1/share?target_type=post",
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["target_type"] == "post"

    async def test_list_shares_with_pagination(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试分页功能"""
        from app.services.share_service import create_share

        # 创建5条记录
        for i in range(5):
            await create_share(
                db_session,
                user_id=test_user.id,
                target_type="post",
                target_id=f"post_{i}",
                share_channel="wechat_friend",
            )

        # 第一页：2条
        response = client.get(
            "/api/v1/share?limit=2&offset=0",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

        # 第二页：2条
        response = client.get(
            "/api/v1/share?limit=2&offset=2",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_shares_limit_validation(self, client, test_user: User, user_headers: dict):
        """测试分页限制参数验证"""
        # limit 超过最大值
        response = client.get(
            "/api/v1/share?limit=100",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # limit 为负数
        response = client.get(
            "/api/v1/share?limit=-1",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # offset 为负数
        response = client.get(
            "/api/v1/share?offset=-1",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_shares_empty_result(self, client, test_user: User, user_headers: dict):
        """测试空结果"""
        response = client.get("/api/v1/share", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_shares_without_auth(self, client):
        """测试未认证用户获取列表"""
        response = client.get("/api/v1/share")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetShareStatsEndpoint:
    """测试获取分享统计接口"""

    async def test_get_stats_default_7_days(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取默认7天的统计"""
        from app.services.share_service import create_share, update_share_status

        share = await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await update_share_status(db_session, share.id, "success")

        response = client.get("/api/v1/share/stats", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_shares"] == 1
        assert data["success_shares"] == 1
        assert data["success_rate"] == "100.0%"
        assert data["days"] == 7

    async def test_get_stats_custom_days(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试自定义统计天数"""
        from app.services.share_service import create_share

        await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        # 统计30天
        response = client.get(
            "/api/v1/share/stats?days=30",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["days"] == 30

        # 统计1天
        response = client.get(
            "/api/v1/share/stats?days=1",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["days"] == 1

    def test_get_stats_validation(self, client, test_user: User, user_headers: dict):
        """测试参数验证"""
        # days 超过最大值
        response = client.get(
            "/api/v1/share/stats?days=100",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # days 小于最小值
        response = client.get(
            "/api/v1/share/stats?days=0",
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_stats_zero_shares(self, client, test_user: User, user_headers: dict):
        """测试没有分享记录时的统计"""
        response = client.get("/api/v1/share/stats", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_shares"] == 0
        assert data["success_shares"] == 0
        assert data["success_rate"] == "0.0%"

    def test_get_stats_without_auth(self, client):
        """测试未认证用户获取统计"""
        response = client.get("/api/v1/share/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestUpdateShareStatusEndpoint:
    """测试更新分享状态接口"""

    async def test_update_status_to_success(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试更新状态为成功"""
        from app.services.share_service import create_share

        share = await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        response = client.put(
            f"/api/v1/share/{share.id}/status",
            json={"status": "success"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["share_status"] == "success"

    async def test_update_status_to_failed_with_error(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试更新状态为失败并记录错误信息"""
        from app.services.share_service import create_share

        share = await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        response = client.put(
            f"/api/v1/share/{share.id}/status",
            json={
                "status": "failed",
                "error_message": "用户取消分享",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["share_status"] == "failed"

    def test_update_status_nonexistent_share(self, client, test_user: User, user_headers: dict):
        """测试更新不存在的分享记录"""
        response = client.put(
            "/api/v1/share/nonexistent_share_id/status",
            json={"status": "success"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_status_invalid_status_value(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试无效的状态值"""
        from app.services.share_service import create_share

        share = await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        response = client.put(
            f"/api/v1/share/{share.id}/status",
            json={"status": "pending"},  # invalid status
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_status_without_auth(self, client, db_session: AsyncSession):
        """测试未认证用户更新状态"""
        from app.services.share_service import create_share

        share = await create_share(
            db_session,
            user_id="test_user",
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        response = client.put(
            f"/api/v1/share/{share.id}/status",
            json={"status": "success"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_status_optional_error_message(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试error_message为可选字段"""
        from app.services.share_service import create_share

        share = await create_share(
            db_session,
            user_id=test_user.id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        # 不提供 error_message
        response = client.put(
            f"/api/v1/share/{share.id}/status",
            json={"status": "failed"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
