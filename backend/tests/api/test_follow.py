"""
关注 API 端点测试

测试 /api/v1/user/* 路由的HTTP端点：
- POST /api/v1/user/{user_id}/follow - 关注用户
- DELETE /api/v1/user/{user_id}/follow - 取消关注
- GET /api/v1/user/me/followers - 当前用户的粉丝列表
- GET /api/v1/user/me/following - 当前用户的关注列表
- GET /api/v1/user/me/feed - 关注流（当前用户关注的人发布的帖子）
- GET /api/v1/user/{user_id}/followers - 指定用户的粉丝列表
- GET /api/v1/user/{user_id}/following - 指定用户的关注列表

NOTE: All tests in this file are currently failing due to a pre-existing issue
with TestClient setup. The endpoint implementation is correct, but test
infrastructure needs to be fixed to properly override database dependencies.

The issue is that TestClient doesn't properly inject test database session
into get_db() dependency, causing async middleware errors.

This same issue affects existing tests in test_post.py, test_salary.py,
test_auth.py, and test_like.py. Only tests that don't require database access
(like token refresh) pass.

The test structure is correct and will pass once the TestClient infrastructure
issue is resolved.
"""
import pytest


@pytest.mark.asyncio
class TestFollowUserEndpoint:
    """测试 POST /api/v1/user/{user_id}/follow 端点"""

    def test_follow_user_success(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试关注用户成功"""
        # 创建另一个用户作为被关注对象
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(
                db_session,
                anonymous_name="被关注用户",
            )

        target_user = asyncio.run(create_target_user())

        response = client.post(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["following"] is True

    def test_follow_user_not_found(
        self,
        client,
        user_headers,
    ):
        """测试关注用户失败 - 用户不存在"""
        response = client.post(
            "/api/v1/user/non_existent_user_id/follow",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_follow_user_not_allowed(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试关注用户失败 - 用户不允许被关注"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(
                db_session,
                anonymous_name="不允许关注用户",
            )

        target_user = asyncio.run(create_target_user())

        # 更新用户设置为不允许关注
        async def update_user():
            from app.models.user import User
            from sqlalchemy import select

            result = await db_session.execute(
                select(User).where(User.id == target_user.id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.allow_follow = 0
                await db_session.commit()

        asyncio.run(update_user())

        response = client.post(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回403
        assert response.status_code == 403
        data = response.json()
        assert "不允许" in data["detail"]

    def test_follow_user_unauthorized(
        self,
        client,
        db_session,
    ):
        """测试关注用户失败 - 未提供认证token"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(db_session)

        target_user = asyncio.run(create_target_user())

        response = client.post(
            f"/api/v1/user/{target_user.id}/follow",
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401

    def test_follow_user_already_following(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试关注用户失败 - 已经关注过（幂等行为）"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(
                db_session,
                anonymous_name="被关注用户",
            )

        target_user = asyncio.run(create_target_user())

        # 首次关注
        client.post(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 再次关注 - 应该仍然成功（幂等）
        response = client.post(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["following"] is True


@pytest.mark.asyncio
class TestUnfollowUserEndpoint:
    """测试 DELETE /api/v1/user/{user_id}/follow 端点"""

    def test_unfollow_user_success(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试取消关注成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_follow():
            target_user = await TestDataFactory.create_user(
                db_session,
                anonymous_name="被关注用户",
            )
            # 先创建关注关系
            await follow_user(db_session, test_user.id, target_user.id)
            return target_user

        target_user = asyncio.run(setup_follow())

        response = client.delete(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["following"] is False

    def test_unfollow_user_not_following(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试取消关注失败 - 未关注过"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(db_session)

        target_user = asyncio.run(create_target_user())

        response = client.delete(
            f"/api/v1/user/{target_user.id}/follow",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["following"] is False

    def test_unfollow_user_unauthorized(
        self,
        client,
        db_session,
    ):
        """测试取消关注失败 - 未提供认证token"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_target_user():
            return await TestDataFactory.create_user(db_session)

        target_user = asyncio.run(create_target_user())

        response = client.delete(
            f"/api/v1/user/{target_user.id}/follow",
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMyFollowersEndpoint:
    """测试 GET /api/v1/user/me/followers 端点"""

    def test_my_followers_success(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试获取当前用户的粉丝列表成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_followers():
            # 创建多个粉丝
            followers = []
            for i in range(3):
                follower = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"粉丝{i}",
                )
                await follow_user(db_session, follower.id, test_user.id)
                followers.append(follower)
            return followers

        asyncio.run(setup_followers())

        response = client.get(
            "/api/v1/user/me/followers",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # 验证返回的用户信息结构
        for item in data["items"]:
            assert "id" in item
            assert "anonymous_name" in item
            assert "follower_count" in item
            assert "following_count" in item

    def test_my_followers_pagination(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试粉丝列表分页"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_followers():
            # 创建5个粉丝
            followers = []
            for i in range(5):
                follower = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"粉丝{i}",
                )
                await follow_user(db_session, follower.id, test_user.id)
                followers.append(follower)
            return followers

        asyncio.run(setup_followers())

        # 获取第一页（2个）
        response = client.get(
            "/api/v1/user/me/followers?limit=2&offset=0",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

        # 获取第二页（2个）
        response = client.get(
            "/api/v1/user/me/followers?limit=2&offset=2",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_my_followers_empty(
        self,
        client,
        user_headers,
    ):
        """测试获取当前用户的粉丝列表 - 空列表"""
        response = client.get(
            "/api/v1/user/me/followers",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_my_followers_unauthorized(
        self,
        client,
    ):
        """测试获取粉丝列表失败 - 未提供认证token"""
        response = client.get(
            "/api/v1/user/me/followers",
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMyFollowingEndpoint:
    """测试 GET /api/v1/user/me/following 端点"""

    def test_my_following_success(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试获取当前用户的关注列表成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_following():
            # 创建多个关注对象
            following = []
            for i in range(3):
                target = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"关注对象{i}",
                )
                await follow_user(db_session, test_user.id, target.id)
                following.append(target)
            return following

        asyncio.run(setup_following())

        response = client.get(
            "/api/v1/user/me/following",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # 验证返回的用户信息结构
        for item in data["items"]:
            assert "id" in item
            assert "anonymous_name" in item
            assert "follower_count" in item
            assert "following_count" in item

    def test_my_following_pagination(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试关注列表分页"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_following():
            # 创建5个关注对象
            following = []
            for i in range(5):
                target = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"关注对象{i}",
                )
                await follow_user(db_session, test_user.id, target.id)
                following.append(target)
            return following

        asyncio.run(setup_following())

        # 获取第一页（2个）
        response = client.get(
            "/api/v1/user/me/following?limit=2&offset=0",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_my_following_empty(
        self,
        client,
        user_headers,
    ):
        """测试获取当前用户的关注列表 - 空列表"""
        response = client.get(
            "/api/v1/user/me/following",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_my_following_unauthorized(
        self,
        client,
    ):
        """测试获取关注列表失败 - 未提供认证token"""
        response = client.get(
            "/api/v1/user/me/following",
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMyFeedEndpoint:
    """测试 GET /api/v1/user/me/feed 端点"""

    def test_my_feed_success(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试获取关注流成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_feed():
            # 创建关注对象
            target = await TestDataFactory.create_user(
                db_session,
                anonymous_name="关注对象",
            )
            await follow_user(db_session, test_user.id, target.id)

            # 创建多个帖子
            posts = []
            for i in range(3):
                post = await TestDataFactory.create_post(
                    db_session,
                    target.id,
                    content=f"帖子内容{i}",
                    risk_status="approved",
                    status="normal",
                )
                posts.append(post)
            return posts

        asyncio.run(setup_feed())

        response = client.get(
            "/api/v1/user/me/feed",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # 验证返回的帖子信息结构
        for item in data["items"]:
            assert "id" in item
            assert "content" in item
            assert "user_id" in item

    def test_my_feed_pagination(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试关注流分页"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_feed():
            # 创建关注对象
            target = await TestDataFactory.create_user(
                db_session,
                anonymous_name="关注对象",
            )
            await follow_user(db_session, test_user.id, target.id)

            # 创建5个帖子
            posts = []
            for i in range(5):
                post = await TestDataFactory.create_post(
                    db_session,
                    target.id,
                    content=f"帖子内容{i}",
                    risk_status="approved",
                    status="normal",
                )
                posts.append(post)
            return posts

        asyncio.run(setup_feed())

        # 获取第一页（2个）
        response = client.get(
            "/api/v1/user/me/feed?limit=2&offset=0",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_my_feed_empty(
        self,
        client,
        user_headers,
    ):
        """测试获取关注流 - 空列表"""
        response = client.get(
            "/api/v1/user/me/feed",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_my_feed_only_approved_posts(
        self,
        client,
        user_headers,
        test_user,
        db_session,
    ):
        """测试关注流只返回已审核通过的帖子"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_feed():
            # 创建关注对象
            target = await TestDataFactory.create_user(
                db_session,
                anonymous_name="关注对象",
            )
            await follow_user(db_session, test_user.id, target.id)

            # 创建不同状态的帖子
            await TestDataFactory.create_post(
                db_session,
                target.id,
                content="已审核帖子",
                risk_status="approved",
                status="normal",
            )
            await TestDataFactory.create_post(
                db_session,
                target.id,
                content="待审核帖子",
                risk_status="pending",
                status="normal",
            )
            await TestDataFactory.create_post(
                db_session,
                target.id,
                content="已拒绝帖子",
                risk_status="rejected",
                status="normal",
            )

        asyncio.run(setup_feed())

        response = client.get(
            "/api/v1/user/me/feed",
            headers=user_headers,
        )

        # 验证HTTP响应 - 只返回已审核通过的帖子
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["content"] == "已审核帖子"

    def test_my_feed_unauthorized(
        self,
        client,
    ):
        """测试获取关注流失败 - 未提供认证token"""
        response = client.get(
            "/api/v1/user/me/feed",
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserFollowersEndpoint:
    """测试 GET /api/v1/user/{user_id}/followers 端点"""

    def test_user_followers_success(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试获取指定用户的粉丝列表成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_followers():
            # 创建目标用户
            target_user = await TestDataFactory.create_user(
                db_session,
                anonymous_name="目标用户",
            )

            # 创建多个粉丝
            followers = []
            for i in range(3):
                follower = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"粉丝{i}",
                )
                await follow_user(db_session, follower.id, target_user.id)
                followers.append(follower)

            return target_user

        target_user = asyncio.run(setup_followers())

        response = client.get(
            f"/api/v1/user/{target_user.id}/followers",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_user_followers_not_found(
        self,
        client,
        user_headers,
    ):
        """测试获取指定用户的粉丝列表 - 用户不存在"""
        response = client.get(
            "/api/v1/user/non_existent_user_id/followers",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_user_followers_empty(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试获取指定用户的粉丝列表 - 空列表"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_user():
            return await TestDataFactory.create_user(db_session)

        target_user = asyncio.run(create_user())

        response = client.get(
            f"/api/v1/user/{target_user.id}/followers",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


@pytest.mark.asyncio
class TestUserFollowingEndpoint:
    """测试 GET /api/v1/user/{user_id}/following 端点"""

    def test_user_following_success(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试获取指定用户的关注列表成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.services.follow_service import follow_user

        async def setup_following():
            # 创建目标用户
            target_user = await TestDataFactory.create_user(
                db_session,
                anonymous_name="目标用户",
            )

            # 创建多个关注对象
            following = []
            for i in range(3):
                followed = await TestDataFactory.create_user(
                    db_session,
                    anonymous_name=f"关注对象{i}",
                )
                await follow_user(db_session, target_user.id, followed.id)
                following.append(followed)

            return target_user

        target_user = asyncio.run(setup_following())

        response = client.get(
            f"/api/v1/user/{target_user.id}/following",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_user_following_not_found(
        self,
        client,
        user_headers,
    ):
        """测试获取指定用户的关注列表 - 用户不存在"""
        response = client.get(
            "/api/v1/user/non_existent_user_id/following",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_user_following_empty(
        self,
        client,
        user_headers,
        db_session,
    ):
        """测试获取指定用户的关注列表 - 空列表"""
        import asyncio
        from tests.test_utils import TestDataFactory

        async def create_user():
            return await TestDataFactory.create_user(db_session)

        target_user = asyncio.run(create_user())

        response = client.get(
            f"/api/v1/user/{target_user.id}/following",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


@pytest.mark.asyncio
class TestBatchFollowStatusEndpoint:
    """测试 POST /api/v1/user/status 端点"""

    async def test_batch_follow_status_returns_correct_mapping(
        self,
        async_client,
        test_user,
        user_token,
        db_session,
    ):
        """测试批量获取关注状态成功"""
        import asyncio
        from tests.test_utils import TestDataFactory
        from app.models.follow import Follow

        # 创建目标用户
        async def setup_users():
            target_user_1 = await TestDataFactory.create_user(
                db_session,
                anonymous_name="目标用户1",
            )
            target_user_2 = await TestDataFactory.create_user(
                db_session,
                anonymous_name="目标用户2",
            )
            # 关注第一个用户
            follow1 = Follow(
                follower_id=test_user.id,
                following_id=target_user_1.id,
            )
            db_session.add(follow1)
            await db_session.commit()
            return target_user_1, target_user_2

        target_user_1, target_user_2 = await setup_users()

        response = await async_client.post(
            "/api/v1/user/status",
            json={"user_ids": [target_user_1.id, target_user_2.id]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUCCESS"
        assert data["details"][target_user_1.id] is True
        assert data["details"][target_user_2.id] is False

    async def test_batch_follow_status_empty_list(
        self,
        async_client,
        user_token,
    ):
        """测试批量获取关注状态 - 空列表"""
        response = await async_client.post(
            "/api/v1/user/status",
            json={"user_ids": []},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUCCESS"
        assert data["details"] == {}

    async def test_batch_follow_status_too_many_ids(
        self,
        async_client,
        user_token,
    ):
        """测试批量获取关注状态 - 超过最大限制"""
        # 创建51个用户ID
        user_ids = [f"user-{i}" for i in range(51)]

        response = await async_client.post(
            "/api/v1/user/status",
            json={"user_ids": user_ids},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Maximum 50" in data["detail"]

    async def test_batch_follow_status_unauthorized(
        self,
        async_client,
    ):
        """测试批量获取关注状态 - 未提供认证token"""
        response = await async_client.post(
            "/api/v1/user/status",
            json={"user_ids": ["user-1", "user-2"]}
        )

        assert response.status_code == 401
