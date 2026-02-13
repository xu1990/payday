"""
Admin API 端点测试

测试 /api/v1/admin/* 路由的HTTP端点：
- POST /api/v1/admin/auth/login - 管理员登录
- GET /api/v1/admin/users - 获取用户列表
- GET /api/v1/admin/users/{id} - 获取用户详情
- GET /api/v1/admin/salary-records - 获取工资记录列表
- DELETE /api/v1/admin/salary-records/{id} - 删除工资记录
- PUT /api/v1/admin/salary-records/{id}/risk - 更新工资记录风控状态
- GET /api/v1/admin/statistics - 获取统计数据
- GET /api/v1/admin/posts - 获取帖子列表
- GET /api/v1/admin/posts/{id} - 获取帖子详情
- PUT /api/v1/admin/posts/{id}/status - 更新帖子状态
- DELETE /api/v1/admin/posts/{id} - 删除帖子
- GET /api/v1/admin/comments - 获取评论列表
- PUT /api/v1/admin/comments/{id}/risk - 更新评论风控状态
"""
import pytest


class TestAdminLoginEndpoint:
    """测试POST /api/v1/admin/auth/login端点"""

    def test_admin_login_success(self, client, test_admin):
        """测试管理员登录成功"""
        response = client.post(
            "/api/v1/admin/auth/login",
            json={
                "username": "test_admin",
                "password": "test_password"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "csrf_token" in data
        assert len(data["access_token"]) > 0
        assert len(data["csrf_token"]) > 0

    def test_admin_login_wrong_password(self, client, test_admin):
        """测试管理员登录失败 - 密码错误"""
        response = client.post(
            "/api/v1/admin/auth/login",
            json={
                "username": "test_admin",
                "password": "wrong_password"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_admin_login_wrong_username(self, client):
        """测试管理员登录失败 - 用户名不存在"""
        response = client.post(
            "/api/v1/admin/auth/login",
            json={
                "username": "non_existent_admin",
                "password": "test_password"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_admin_login_missing_fields(self, client):
        """测试管理员登录失败 - 缺少必填字段"""
        response = client.post(
            "/api/v1/admin/auth/login",
            json={
                "username": "test_admin"
                # 缺少password
            }
        )

        # 验证HTTP响应
        assert response.status_code == 422


class TestAdminUserListEndpoint:
    """测试GET /api/v1/admin/users端点"""

    def test_list_users_success(self, client, admin_headers, test_user):
        """测试管理员获取用户列表成功"""
        response = client.get("/api/v1/admin/users", headers=admin_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

        # 验证用户列表项结构
        if len(data["items"]) > 0:
            user = data["items"][0]
            assert "id" in user
            assert "openid" in user
            assert "anonymous_name" in user
            assert "status" in user
            assert "created_at" in user

    def test_list_users_with_pagination(self, client, admin_headers):
        """测试获取用户列表 - 分页参数"""
        response = client.get(
            "/api/v1/admin/users?limit=1&offset=0",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 1

    def test_list_users_with_keyword(self, client, admin_headers, test_user):
        """测试获取用户列表 - 按昵称关键词搜索"""
        response = client.get(
            f"/api/v1/admin/users?keyword={test_user.anonymous_name}",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_users_with_status(self, client, admin_headers):
        """测试获取用户列表 - 按状态筛选"""
        response = client.get(
            "/api/v1/admin/users?status=normal",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_users_unauthorized(self, client, user_headers):
        """测试获取用户列表失败 - 普通用户无权限"""
        response = client.get("/api/v1/admin/users", headers=user_headers)

        # 验证HTTP响应 - 应该返回401或403
        assert response.status_code in [401, 403]

    def test_list_users_no_auth(self, client):
        """测试获取用户列表失败 - 未认证"""
        response = client.get("/api/v1/admin/users")

        # 验证HTTP响应
        assert response.status_code == 401


class TestAdminUserDetailEndpoint:
    """测试GET /api/v1/admin/users/{user_id}端点"""

    def test_get_user_detail_success(self, client, admin_headers, test_user):
        """测试管理员获取用户详情成功"""
        response = client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["openid"] == test_user.openid
        assert data["anonymous_name"] == test_user.anonymous_name
        assert "status" in data
        assert "created_at" in data
        assert "follower_count" in data
        assert "following_count" in data
        assert "post_count" in data

    def test_get_user_detail_not_found(self, client, admin_headers):
        """测试获取用户详情失败 - 用户不存在"""
        response = client.get(
            "/api/v1/admin/users/non_existent_user_id",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_get_user_detail_unauthorized(self, client, user_headers, test_user):
        """测试获取用户详情失败 - 普通用户无权限"""
        response = client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminSalaryListEndpoint:
    """测试GET /api/v1/admin/salary-records端点"""

    def test_list_salary_records_success(
        self, client, admin_headers, test_salary
    ):
        """测试管理员获取工资记录列表成功"""
        response = client.get("/api/v1/admin/salary-records", headers=admin_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

        # 验证工资记录结构
        if len(data["items"]) > 0:
            record = data["items"][0]
            assert "id" in record
            assert "user_id" in record
            assert "config_id" in record
            assert "amount" in record
            assert "payday_date" in record
            assert "salary_type" in record
            assert "risk_status" in record
            assert "created_at" in record

    def test_list_salary_records_with_user_filter(
        self, client, admin_headers, test_salary, test_user
    ):
        """测试获取工资记录列表 - 按user_id过滤"""
        response = client.get(
            f"/api/v1/admin/salary-records?user_id={test_user.id}",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_salary_records_with_pagination(
        self, client, admin_headers, test_salary
    ):
        """测试获取工资记录列表 - 分页参数"""
        response = client.get(
            "/api/v1/admin/salary-records?limit=1&offset=0",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    def test_list_salary_records_unauthorized(self, client, user_headers):
        """测试获取工资记录列表失败 - 普通用户无权限"""
        response = client.get("/api/v1/admin/salary-records", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminSalaryDeleteEndpoint:
    """测试DELETE /api/v1/admin/salary-records/{record_id}端点"""

    def test_delete_salary_record_success(
        self, client, admin_headers, db_session, test_user
    ):
        """测试管理员删除工资记录成功"""
        # 先创建一个工资记录
        from tests.test_utils import TestDataFactory
        from app.models.payday import PaydayConfig

        config = PaydayConfig(
            user_id=test_user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        salary = TestDataFactory.create_salary(db_session, test_user.id, config.id)

        # 删除记录（需要CSRF token）
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            f"/api/v1/admin/salary-records/{salary.id}",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 204

    def test_delete_salary_record_not_found(self, client, admin_headers):
        """测试删除工资记录失败 - 记录不存在"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            "/api/v1/admin/salary-records/non_existent_record_id",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_delete_salary_record_unauthorized(self, client, user_headers):
        """测试删除工资记录失败 - 普通用户无权限"""
        headers_with_csrf = user_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            "/api/v1/admin/salary-records/some_record_id",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminSalaryUpdateRiskEndpoint:
    """测试PUT /api/v1/admin/salary-records/{record_id}/risk端点"""

    def test_update_salary_risk_success(
        self, client, admin_headers, test_salary
    ):
        """测试管理员更新工资记录风控状态成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/salary-records/{test_salary.id}/risk",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["risk_status"] == "approved"

    def test_update_salary_risk_rejected(
        self, client, admin_headers, test_salary
    ):
        """测试管理员拒绝工资记录"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/salary-records/{test_salary.id}/risk",
            json={"risk_status": "rejected"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["risk_status"] == "rejected"

    def test_update_salary_risk_not_found(self, client, admin_headers):
        """测试更新工资记录风控状态失败 - 记录不存在"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            "/api/v1/admin/salary-records/non_existent_record_id/risk",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 404

    def test_update_salary_risk_invalid_status(
        self, client, admin_headers, test_salary
    ):
        """测试更新工资记录风控状态失败 - 无效的状态值"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/salary-records/{test_salary.id}/risk",
            json={"risk_status": "invalid_status"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422


class TestAdminStatisticsEndpoint:
    """测试GET /api/v1/admin/statistics端点"""

    def test_get_statistics_success(self, client, admin_headers):
        """测试管理员获取统计数据成功"""
        response = client.get("/api/v1/admin/statistics", headers=admin_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "user_total" in data
        assert "user_new_today" in data
        assert "salary_record_total" in data
        assert "salary_record_today" in data
        assert isinstance(data["user_total"], int)
        assert isinstance(data["user_new_today"], int)
        assert isinstance(data["salary_record_total"], int)
        assert isinstance(data["salary_record_today"], int)

    def test_get_statistics_unauthorized(self, client, user_headers):
        """测试获取统计数据失败 - 普通用户无权限"""
        response = client.get("/api/v1/admin/statistics", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminPostListEndpoint:
    """测试GET /api/v1/admin/posts端点"""

    def test_list_posts_success(self, client, admin_headers, test_post):
        """测试管理员获取帖子列表成功"""
        response = client.get("/api/v1/admin/posts", headers=admin_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

        # 验证帖子列表项结构
        if len(data["items"]) > 0:
            post = data["items"][0]
            assert "id" in post
            assert "user_id" in post
            assert "anonymous_name" in post
            assert "content" in post
            assert "type" in post
            assert "view_count" in post
            assert "like_count" in post
            assert "comment_count" in post
            assert "status" in post
            assert "risk_status" in post
            assert "created_at" in post

    def test_list_posts_with_status_filter(self, client, admin_headers, test_post):
        """测试获取帖子列表 - 按status筛选"""
        response = client.get(
            "/api/v1/admin/posts?status=normal",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_posts_with_risk_status_filter(
        self, client, admin_headers, test_post
    ):
        """测试获取帖子列表 - 按risk_status筛选（风控待审）"""
        response = client.get(
            "/api/v1/admin/posts?risk_status=pending",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_posts_with_pagination(self, client, admin_headers):
        """测试获取帖子列表 - 分页参数"""
        response = client.get(
            "/api/v1/admin/posts?limit=1&offset=0",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    def test_list_posts_unauthorized(self, client, user_headers):
        """测试获取帖子列表失败 - 普通用户无权限"""
        response = client.get("/api/v1/admin/posts", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminPostDetailEndpoint:
    """测试GET /api/v1/admin/posts/{post_id}端点"""

    def test_get_post_detail_success(self, client, admin_headers, test_post):
        """测试管理员获取帖子详情成功"""
        response = client.get(
            f"/api/v1/admin/posts/{test_post.id}",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_post.id)
        assert data["user_id"] == str(test_post.user_id)
        assert "content" in data
        assert "status" in data
        assert "risk_status" in data

    def test_get_post_detail_not_found(self, client, admin_headers):
        """测试获取帖子详情失败 - 帖子不存在"""
        response = client.get(
            "/api/v1/admin/posts/non_existent_post_id",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_get_post_detail_unauthorized(self, client, user_headers, test_post):
        """测试获取帖子详情失败 - 普通用户无权限"""
        response = client.get(
            f"/api/v1/admin/posts/{test_post.id}",
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminPostUpdateStatusEndpoint:
    """测试PUT /api/v1/admin/posts/{post_id}/status端点"""

    def test_update_post_status_hidden(self, client, admin_headers, test_post):
        """测试管理员隐藏帖子成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/posts/{test_post.id}/status",
            json={"status": "hidden"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["id"] == str(test_post.id)

    def test_update_post_status_normal(self, client, admin_headers, test_post):
        """测试管理员恢复帖子成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/posts/{test_post.id}/status",
            json={"status": "normal"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_update_post_risk_status_approved(
        self, client, admin_headers, test_post
    ):
        """测试管理员通过帖子审核成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/posts/{test_post.id}/status",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_update_post_risk_status_rejected(
        self, client, admin_headers, test_post
    ):
        """测试管理员拒绝帖子审核成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/posts/{test_post.id}/status",
            json={
                "risk_status": "rejected",
                "risk_reason": "测试拒绝原因"
            },
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_update_post_status_not_found(self, client, admin_headers):
        """测试更新帖子状态失败 - 帖子不存在"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            "/api/v1/admin/posts/non_existent_post_id/status",
            json={"status": "hidden"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 404

    def test_update_post_status_unauthorized(self, client, user_headers):
        """测试更新帖子状态失败 - 普通用户无权限"""
        headers_with_csrf = user_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            "/api/v1/admin/posts/some_post_id/status",
            json={"status": "hidden"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminPostDeleteEndpoint:
    """测试DELETE /api/v1/admin/posts/{post_id}端点"""

    def test_delete_post_success(self, client, admin_headers, test_post):
        """测试管理员删除帖子成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            f"/api/v1/admin/posts/{test_post.id}",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 204

    def test_delete_post_not_found(self, client, admin_headers):
        """测试删除帖子失败 - 帖子不存在"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            "/api/v1/admin/posts/non_existent_post_id",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 404

    def test_delete_post_unauthorized(self, client, user_headers):
        """测试删除帖子失败 - 普通用户无权限"""
        headers_with_csrf = user_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.delete(
            "/api/v1/admin/posts/some_post_id",
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminCommentListEndpoint:
    """测试GET /api/v1/admin/comments端点"""

    def test_list_comments_success(self, client, admin_headers, test_comment):
        """测试管理员获取评论列表成功"""
        response = client.get("/api/v1/admin/comments", headers=admin_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

        # 验证评论列表项结构
        if len(data["items"]) > 0:
            comment = data["items"][0]
            assert "id" in comment
            assert "post_id" in comment
            assert "user_id" in comment
            assert "anonymous_name" in comment
            assert "content" in comment
            assert "parent_id" in comment
            assert "like_count" in comment
            assert "risk_status" in comment
            assert "created_at" in comment

    def test_list_comments_with_post_filter(
        self, client, admin_headers, test_comment
    ):
        """测试获取评论列表 - 按post_id筛选"""
        response = client.get(
            f"/api/v1/admin/comments?post_id={test_comment.post_id}",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_comments_with_risk_status_filter(
        self, client, admin_headers, test_comment
    ):
        """测试获取评论列表 - 按risk_status筛选（风控待审）"""
        response = client.get(
            "/api/v1/admin/comments?risk_status=pending",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_comments_with_pagination(self, client, admin_headers):
        """测试获取评论列表 - 分页参数"""
        response = client.get(
            "/api/v1/admin/comments?limit=1&offset=0",
            headers=admin_headers
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    def test_list_comments_unauthorized(self, client, user_headers):
        """测试获取评论列表失败 - 普通用户无权限"""
        response = client.get("/api/v1/admin/comments", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestAdminCommentUpdateRiskEndpoint:
    """测试PUT /api/v1/admin/comments/{comment_id}/risk端点"""

    def test_update_comment_risk_approved(
        self, client, admin_headers, test_comment
    ):
        """测试管理员通过评论审核成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/comments/{test_comment.id}/risk",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["id"] == str(test_comment.id)

    def test_update_comment_risk_rejected(
        self, client, admin_headers, test_comment
    ):
        """测试管理员拒绝评论审核成功"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/comments/{test_comment.id}/risk",
            json={
                "risk_status": "rejected",
                "risk_reason": "测试拒绝原因"
            },
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_update_comment_risk_not_found(self, client, admin_headers):
        """测试更新评论风控状态失败 - 评论不存在"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            "/api/v1/admin/comments/non_existent_comment_id/risk",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code == 404

    def test_update_comment_risk_invalid_status(
        self, client, admin_headers, test_comment
    ):
        """测试更新评论风控状态失败 - 无效的状态值"""
        headers_with_csrf = admin_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            f"/api/v1/admin/comments/{test_comment.id}/risk",
            json={"risk_status": "invalid_status"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422

    def test_update_comment_risk_unauthorized(self, client, user_headers):
        """测试更新评论风控状态失败 - 普通用户无权限"""
        headers_with_csrf = user_headers.copy()
        headers_with_csrf["X-CSRF-Token"] = "test_csrf_token"

        response = client.put(
            "/api/v1/admin/comments/some_comment_id/risk",
            json={"risk_status": "approved"},
            headers=headers_with_csrf
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]
