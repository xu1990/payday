"""用户API测试"""
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post
from app.models.checkin import CheckIn
from app.models.follow import Follow
from tests.test_utils import TestDataFactory


@pytest.mark.asyncio
class TestGetMe:
    """测试获取当前用户信息"""

    def test_get_me_success(self, client, test_user: User, user_headers: dict):
        """测试成功获取当前用户信息"""
        response = client.get("/api/v1/user/me", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["anonymous_name"] == test_user.anonymous_name
        assert "avatar" in data
        assert "bio" in data
        assert "follower_count" in data
        assert "following_count" in data
        assert "post_count" in data
        assert "allow_follow" in data
        assert "allow_comment" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_me_unauthorized(self, client):
        """测试未认证用户获取信息返回401"""
        response = client.get("/api/v1/user/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestUpdateMe:
    """测试更新当前用户信息"""

    def test_update_me_anonymous_name(self, client, test_user: User, user_headers: dict):
        """测试更新昵称"""
        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json={"anonymous_name": "新昵称"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["anonymous_name"] == "新昵称"

    def test_update_me_bio(self, client, test_user: User, user_headers: dict):
        """测试更新简介"""
        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json={"bio": "这是我的新简介"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["bio"] == "这是我的新简介"

    def test_update_me_avatar(self, client, test_user: User, user_headers: dict):
        """测试更新头像"""
        new_avatar = "https://example.com/new-avatar.jpg"
        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json={"avatar": new_avatar}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["avatar"] == new_avatar

    def test_update_me_multiple_fields(self, client, test_user: User, user_headers: dict):
        """测试同时更新多个字段"""
        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json={
                "anonymous_name": "更新后的昵称",
                "bio": "更新后的简介",
                "avatar": "https://example.com/avatar.jpg"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["anonymous_name"] == "更新后的昵称"
        assert data["bio"] == "更新后的简介"
        assert data["avatar"] == "https://example.com/avatar.jpg"

    def test_update_me_empty_body(self, client, test_user: User, user_headers: dict):
        """测试空请求体不更新任何字段"""
        original_name = test_user.anonymous_name
        original_bio = test_user.bio

        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json={}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 验证字段未改变
        assert data["anonymous_name"] == original_name
        assert data["bio"] == original_bio

    def test_update_me_unauthorized(self, client):
        """测试未认证用户更新信息返回401"""
        response = client.put(
            "/api/v1/user/me",
            json={"anonymous_name": "新昵称"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetProfileData:
    """测试获取用户主页数据"""

    async def test_get_profile_data_success(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试成功获取用户主页数据"""
        # 创建测试数据
        await TestDataFactory.create_post(
            db_session,
            test_user.id,
            content="测试帖子",
            status="normal",
            risk_status="approved"
        )

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "posts" in data
        assert "checkins" in data
        assert "follower_count" in data
        assert "following_count" in data
        assert isinstance(data["posts"], list)
        assert isinstance(data["checkins"], list)
        assert isinstance(data["follower_count"], int)
        assert isinstance(data["following_count"], int)

    async def test_get_profile_data_with_posts(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取包含帖子的主页数据"""
        # 创建3篇帖子
        for i in range(3):
            await TestDataFactory.create_post(
                db_session,
                test_user.id,
                content=f"测试内容{i}",
                status="normal",
                risk_status="approved"
            )

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["posts"]) == 3

    async def test_get_profile_data_with_checkins(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取包含打卡记录的主页数据"""
        from datetime import date

        # 创建5条打卡记录
        for i in range(5):
            checkin = CheckIn(
                user_id=test_user.id,
                check_date=date(2025, 1, i + 1),
            )
            db_session.add(checkin)
        await db_session.commit()

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["checkins"]) == 5

    async def test_get_profile_data_with_followers(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取包含粉丝数的主页数据"""
        # 创建3个粉丝
        for i in range(3):
            follower = await TestDataFactory.create_user(db_session)
            follow = Follow(
                follower_id=follower.id,
                following_id=test_user.id,
            )
            db_session.add(follow)
        await db_session.commit()

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["follower_count"] == 3

    async def test_get_profile_data_with_following(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取包含关注数的主页数据"""
        # 关注3个用户
        for i in range(3):
            following = await TestDataFactory.create_user(db_session)
            follow = Follow(
                follower_id=test_user.id,
                following_id=following.id,
            )
            db_session.add(follow)
        await db_session.commit()

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["following_count"] == 3

    async def test_get_profile_data_only_normal_posts(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试只返回状态为normal的帖子"""
        # 创建不同状态的帖子
        await TestDataFactory.create_post(
            db_session,
            test_user.id,
            content="正常帖子",
            status="normal",
            risk_status="approved"
        )
        await TestDataFactory.create_post(
            db_session,
            test_user.id,
            content="已删除帖子",
            status="deleted",
            risk_status="approved"
        )
        await TestDataFactory.create_post(
            db_session,
            test_user.id,
            content="待审核帖子",
            status="normal",
            risk_status="pending"
        )

        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 应只返回状态为normal且风险审核通过的帖子
        assert len(data["posts"]) == 1

    def test_get_profile_data_empty_user(self, client, test_user: User, user_headers: dict):
        """测试获取空数据用户的主页数据"""
        response = client.get(
            f"/api/v1/user/profile-data/{test_user.id}",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["posts"] == []
        assert data["checkins"] == []
        assert data["follower_count"] == 0
        assert data["following_count"] == 0

    def test_get_profile_data_unauthorized(self, client, test_user: User):
        """测试未认证用户获取主页数据返回401"""
        response = client.get(f"/api/v1/user/profile-data/{test_user.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
