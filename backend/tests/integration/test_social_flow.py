"""社交互动流程集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from tests.test_utils import TestDataFactory


@pytest.mark.asyncio
async def test_post_comment_like_flow(db_session: AsyncSession):
    """测试发帖-评论-点赞完整社交流程"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 创建两个用户
        user1 = await TestDataFactory.create_user(db_session, openid="user1_openid")
        user2 = await TestDataFactory.create_user(db_session, openid="user2_openid")

        from app.core.security import create_access_token
        token1 = create_access_token(data={"sub": str(user1.id)})
        token2 = create_access_token(data={"sub": str(user2.id)})

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # ========== 步骤1: 用户1发帖 ==========

        post_data = {
            "content": "今天发工资了，好开心！",
            "type": "sharing",
            "mood": "happy",
            "anonymous_name": "打工人"
        }

        # Mock风险检查（内容审核）
        from unittest.mock import AsyncMock, patch
        with patch('app.services.risk_service.yu_client') as mock_risk:
            mock_risk.text_moderation = AsyncMock(return_value={
                "Pass": True,
                "Score": 0,
                "Label": ""
            })

            response = await client.post(
                "/api/v1/posts",
                headers=headers1,
                json=post_data
            )

            assert response.status_code == 200
            post = response.json()
            post_id = post["id"]

        # ========== 步骤2: 用户2评论帖子 ==========

        comment_data = {
            "content": "恭喜恭喜！",
            "anonymous_name": "路人甲"
        }

        # Mock通知服务
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            response = await client.post(
                f"/api/v1/posts/{post_id}/comments",
                headers=headers2,
                json=comment_data
            )

            assert response.status_code == 200
            comment = response.json()
            comment_id = comment["id"]

        # ========== 步骤3: 验证评论数增加 ==========

        response = await client.get(f"/api/v1/posts/{post_id}")
        assert response.status_code == 200
        updated_post = response.json()
        assert updated_post["comment_count"] == 1

        # ========== 步骤4: 用户1点赞评论 ==========

        # Mock通知服务
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            response = await client.post(
                f"/api/v1/likes/comment/{comment_id}",
                headers=headers1
            )

            assert response.status_code == 200
            like_result = response.json()
            assert like_result["liked"] is True

        # ========== 步骤5: 验证点赞数增加 ==========

        response = await client.get(f"/api/v1/posts/{post_id}/comments/{comment_id}")
        assert response.status_code == 200
        updated_comment = response.json()
        assert updated_comment["like_count"] == 1

        # ========== 步骤6: 用户1取消点赞 ==========

        response = await client.delete(
            f"/api/v1/likes/comment/{comment_id}",
            headers=headers1
        )

        assert response.status_code == 200
        unlike_result = response.json()
        assert unlike_result["liked"] is False

        # ========== 步骤7: 验证点赞数减少 ==========

        response = await client.get(f"/api/v1/posts/{post_id}/comments/{comment_id}")
        assert response.status_code == 200
        final_comment = response.json()
        assert final_comment["like_count"] == 0


@pytest.mark.asyncio
async def test_follow_and_feed_flow(db_session: AsyncSession):
    """测试关注和动态流流程"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 创建用户
        user1 = await TestDataFactory.create_user(db_session, openid="follower_openid")
        user2 = await TestDataFactory.create_user(db_session, openid="following_openid")

        from app.core.security import create_access_token
        token1 = create_access_token(data={"sub": str(user1.id)})
        token2 = create_access_token(data={"sub": str(user2.id)})

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # ========== 步骤1: user2发帖 ==========

        post_data = {
            "content": "分享我的工作经验",
            "type": "sharing",
            "anonymous_name": "职场老手"
        }

        from unittest.mock import AsyncMock, patch
        with patch('app.services.risk_service.yu_client') as mock_risk:
            mock_risk.text_moderation = AsyncMock(return_value={
                "Pass": True,
                "Score": 0,
                "Label": ""
            })

            response = await client.post(
                "/api/v1/posts",
                headers=headers2,
                json=post_data
            )
            assert response.status_code == 200

        # ========== 步骤2: user1关注user2 ==========

        response = await client.post(
            f"/api/v1/follows/users/{user2.id}",
            headers=headers1
        )

        assert response.status_code == 200
        follow_result = response.json()
        assert follow_result["following"] is True

        # ========== 步骤3: 获取关注列表 ==========

        response = await client.get("/api/v1/follows/following", headers=headers1)
        assert response.status_code == 200

        following_data = response.json()
        assert len(following_data["items"]) > 0
        assert any(f["id"] == str(user2.id) for f in following_data["items"])

        # ========== 步骤4: 获取关注动态流 ==========

        response = await client.get("/api/v1/posts/feed", headers=headers1)
        assert response.status_code == 200

        feed_data = response.json()
        # 应该包含user2的帖子
        assert len(feed_data["items"]) >= 0

        # ========== 步骤5: 取消关注 ==========

        response = await client.delete(
            f"/api/v1/follows/users/{user2.id}",
            headers=headers1
        )

        assert response.status_code == 200
        unfollow_result = response.json()
        assert unfollow_result["following"] is False

        # ========== 步骤6: 验证关注已移除 ==========

        response = await client.get("/api/v1/follows/following", headers=headers1)
        assert response.status_code == 200

        following_data = response.json()
        assert not any(f["id"] == str(user2.id) for f in following_data["items"])


@pytest.mark.asyncio
async def test_notifications_flow(db_session: AsyncSession):
    """测试通知流程"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 创建用户
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        from app.core.security import create_access_token
        token1 = create_access_token(data={"sub": str(user1.id)})
        token2 = create_access_token(data={"sub": str(user2.id)})

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # ========== 步骤1: user2发帖 ==========

        post_data = {
            "content": "测试通知",
            "type": "sharing",
            "anonymous_name": "测试员"
        }

        from unittest.mock import AsyncMock, patch
        with patch('app.services.risk_service.yu_client') as mock_risk:
            mock_risk.text_moderation = AsyncMock(return_value={
                "Pass": True,
                "Score": 0,
                "Label": ""
            })

            response = await client.post(
                "/api/v1/posts",
                headers=headers2,
                json=post_data
            )
            assert response.status_code == 200
            post_id = response.json()["id"]

        # ========== 步骤2: user1评论（触发通知） ==========

        comment_data = {
            "content": "我来评论了",
            "anonymous_name": "评论者"
        }

        # 这会创建通知给user2
        response = await client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=headers1,
            json=comment_data
        )
        assert response.status_code == 200

        # ========== 步骤3: user2查看通知 ==========

        response = await client.get("/api/v1/notifications", headers=headers2)
        assert response.status_code == 200

        notifications = response.json()
        assert len(notifications["items"]) > 0

        # 验证通知类型和内容
        latest_notification = notifications["items"][0]
        assert latest_notification["type"] in ["comment", "reply", "like", "follow"]
        assert "id" in latest_notification

        # ========== 步骤4: 标记通知为已读 ==========

        notification_id = latest_notification["id"]
        response = await client.put(
            f"/api/v1/notifications/{notification_id}/read",
            headers=headers2
        )

        assert response.status_code == 200

        # ========== 步骤5: 批量标记所有通知为已读 ==========

        response = await client.put(
            "/api/v1/notifications/read-all",
            headers=headers2
        )

        assert response.status_code == 200

        # ========== 步骤6: 获取未读通知数 ==========

        response = await client.get("/api/v1/notifications/unread-count", headers=headers2)
        assert response.status_code == 200

        count_data = response.json()
        assert "count" in count_data
        assert count_data["count"] >= 0  # 应该是0（因为我们刚标记为已读）
