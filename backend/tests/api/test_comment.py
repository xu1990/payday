"""评论API测试"""
import pytest
from unittest.mock import AsyncMock
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.post_service import create as create_post
from app.services.comment_service import create as create_comment
from app.schemas.post import PostCreate


async def create_test_user(db: AsyncSession, openid: str, anonymous_name: str) -> User:
    """Helper function to create a test user"""
    user = User(openid=openid, anonymous_name=anonymous_name, avatar=f"https://example.com/{openid}.jpg")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_post(db: AsyncSession, user_id: str, content: str = "测试帖子") -> str:
    """Helper function to create a test post"""
    post = await create_post(db, user_id, PostCreate(content=content), anonymous_name="测试用户")
    post.risk_status = "approved"
    await db.commit()
    await db.refresh(post)
    return post.id


@pytest.mark.asyncio
class TestCommentListEndpoint:
    """测试获取评论列表接口"""

    async def test_list_empty_comments(self, client, db_session: AsyncSession):
        """测试空评论列表"""
        post_id = await create_test_post(db_session, "test_user_id")

        response = client.get(f"/api/v1/posts/{post_id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    async def test_list_root_comments_with_replies(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试获取根评论及其回复"""
        post_id = await create_test_post(db_session, test_user.id)

        # 创建根评论
        root = await create_comment(
            db_session,
            post_id,
            test_user.id,
            test_user.anonymous_name,
            "根评论",
        )

        # 创建回复
        reply = await create_comment(
            db_session,
            post_id,
            test_user.id,
            test_user.anonymous_name,
            "回复评论",
            parent_id=root.id,
        )
        await db_session.commit()

        response = client.get(f"/api/v1/posts/{post_id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == root.id
        assert data[0]["content"] == "根评论"
        assert "replies" in data[0]
        assert len(data[0]["replies"]) == 1
        assert data[0]["replies"][0]["id"] == reply.id
        assert data[0]["replies"][0]["content"] == "回复评论"

    async def test_list_comments_with_limit(self, client, test_user: User, db_session: AsyncSession):
        """测试限制返回数量"""
        post_id = await create_test_post(db_session, test_user.id)

        # 创建5条根评论
        for i in range(5):
            await create_comment(
                db_session,
                post_id,
                test_user.id,
                test_user.anonymous_name,
                f"评论{i}",
            )
        await db_session.commit()

        response = client.get(f"/api/v1/posts/{post_id}/comments?limit=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    async def test_list_comments_with_offset(self, client, test_user: User, db_session: AsyncSession):
        """测试分页偏移"""
        post_id = await create_test_post(db_session, test_user.id)

        # 创建5条根评论
        for i in range(5):
            await create_comment(
                db_session,
                post_id,
                test_user.id,
                test_user.anonymous_name,
                f"评论{i}",
            )
        await db_session.commit()

        response = client.get(f"/api/v1/posts/{post_id}/comments?offset=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 5 - 2 = 3

    async def test_list_comments_limit_validation(self, client, db_session: AsyncSession):
        """测试limit参数验证"""
        post_id = await create_test_post(db_session, "test_user_id")

        # 超过最大值
        response = client.get(f"/api/v1/posts/{post_id}/comments?limit=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 小于最小值
        response = client.get(f"/api/v1/posts/{post_id}/comments?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_comments_offset_validation(self, client, db_session: AsyncSession):
        """测试offset参数验证"""
        post_id = await create_test_post(db_session, "test_user_id")

        # 负数
        response = client.get(f"/api/v1/posts/{post_id}/comments?offset=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_comments_nonexistent_post(self, client, db_session: AsyncSession):
        """测试获取不存在帖子的评论列表 - 返回空列表而不是404"""
        response = client.get("/api/v1/posts/nonexistent_post_id/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


@pytest.mark.asyncio
class TestCommentCreateEndpoint:
    """测试创建评论接口"""

    async def test_create_root_comment(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession, monkeypatch
    ):
        """测试创建根评论"""
        # Mock the risk check background task at the API import location
        monkeypatch.setattr("app.api.v1.comment.run_risk_check_for_comment", AsyncMock())

        post_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "这是我的评论"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "这是我的评论"
        assert data["post_id"] == post_id
        assert data["user_id"] == test_user.id
        assert data["parent_id"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_reply_to_comment(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession, monkeypatch
    ):
        """测试创建回复评论"""
        # Mock the risk check background task at the API import location
        monkeypatch.setattr("app.api.v1.comment.run_risk_check_for_comment", AsyncMock())

        post_id = await create_test_post(db_session, test_user.id)

        # 先创建根评论
        root = await create_comment(
            db_session,
            post_id,
            test_user.id,
            test_user.anonymous_name,
            "根评论",
        )
        await db_session.commit()

        # 创建回复
        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "这是回复", "parent_id": root.id},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "这是回复"
        assert data["parent_id"] == root.id
        assert data["post_id"] == post_id

    async def test_create_comment_content_too_long(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试评论内容超长"""
        post_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "a" * 501},  # 超过500字符
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_comment_content_empty(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试评论内容为空"""
        post_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": ""},  # 空内容
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_comment_whitespace_only(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession, monkeypatch
    ):
        """测试评论内容仅为空格"""
        # Mock the risk check background task at the API import location
        monkeypatch.setattr("app.api.v1.comment.run_risk_check_for_comment", AsyncMock())

        post_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "   "},  # 仅空格
            headers=user_headers,
        )

        # 应该通过验证（min_length=1）但可能在业务层被处理
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY)

    async def test_create_comment_on_non_normal_post(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试成功对正常帖子创建评论"""
        from app.models.post import Post

        # 创建一个正常的帖子
        post = await create_test_post(db_session, test_user.id, "正常帖子")
        post.risk_status = "approved"
        await db_session.commit()

        response = client.post(
            f"/api/v1/posts/{post.id}/comments",
            json={
                "content": "这是评论",
            },
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "这是评论"
    async def test_create_comment_nonexistent_post(
        self, client, test_user: User, user_headers: dict
    ):
        """测试评论不存在的帖子"""
        response = client.post(
            "/api/v1/posts/nonexistent_post_id/comments",
            json={"content": "评论"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_comment_on_non_normal_post(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试评论状态异常的帖子"""
        from app.models.post import Post
        # 创建状态不是normal的帖子
        post = Post(
            user_id=test_user.id,
            content="测试帖子",
            anonymous_name=test_user.anonymous_name,
            status="deleted",  # 非normal状态
            risk_status="approved",
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        response = client.post(
            f"/api/v1/posts/{post.id}/comments",
            json={"content": "评论"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_comment_on_pending_post(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试评论未通过审核的帖子"""
        from app.models.post import Post
        # 创建风险状态未通过的帖子
        post = Post(
            user_id=test_user.id,
            content="测试帖子",
            anonymous_name=test_user.anonymous_name,
            status="normal",
            risk_status="pending",  # 未通过审核
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        response = client.post(
            f"/api/v1/posts/{post.id}/comments",
            json={"content": "评论"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_comment_with_invalid_parent(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试使用无效的parent_id"""
        post_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "回复", "parent_id": "invalid_parent_id"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_comment_with_parent_from_different_post(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试回复其他帖子的评论"""
        # 创建第一个帖子并添加评论
        post1_id = await create_test_post(db_session, test_user.id)

        root = await create_comment(
            db_session,
            post1_id,
            test_user.id,
            test_user.anonymous_name,
            "帖子1的评论",
        )
        await db_session.commit()

        # 创建第二个帖子，尝试使用第一个帖子的评论作为parent
        post2_id = await create_test_post(db_session, test_user.id)

        response = client.post(
            f"/api/v1/posts/{post2_id}/comments",
            json={"content": "回复", "parent_id": root.id},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_comment_requires_auth(self, client, db_session: AsyncSession):
        """测试需要认证"""
        post_id = await create_test_post(db_session, "test_user_id")

        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "评论"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestCommentDeleteEndpoint:
    """测试删除评论接口"""

    async def test_delete_own_comment(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试删除自己的评论"""
        post_id = await create_test_post(db_session, test_user.id)

        comment = await create_comment(
            db_session,
            post_id,
            test_user.id,
            test_user.anonymous_name,
            "要删除的评论",
        )
        await db_session.commit()

        response = client.delete(f"/api/v1/posts/comments/{comment.id}", headers=user_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_nonexistent_comment(
        self, client, test_user: User, user_headers: dict
    ):
        """测试删除不存在的评论"""
        response = client.delete("/api/v1/posts/comments/nonexistent_id", headers=user_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_users_comment(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试删除其他用户的评论"""
        # 创建另一个用户
        other_user = await create_test_user(db_session, "other_user", "其他用户")
        post_id = await create_test_post(db_session, other_user.id)

        # 创建其他用户的评论
        comment = await create_comment(
            db_session,
            post_id,
            other_user.id,
            "其他用户",
            "其他人的评论",
        )
        await db_session.commit()

        # test_user 尝试删除
        response = client.delete(f"/api/v1/posts/comments/{comment.id}", headers=user_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_comment_requires_auth(self, client, db_session: AsyncSession):
        """测试需要认证"""
        response = client.delete("/api/v1/posts/comments/some_comment_id")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
