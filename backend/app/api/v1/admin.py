"""
管理后台 - 登录、用户、工资、统计、帖子/评论管理、风控待审（Sprint 2.4）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, verify_csrf_token, require_permission
from app.core.database import get_db
from app.models.admin import AdminUser
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminUserDetail,
    AdminUserListItem,
    AdminSalaryRecordItem,
    AdminSalaryRecordUpdateRiskRequest,
    AdminStatisticsResponse,
    AdminPostListItem,
    AdminPostListResponse,
    AdminPostUpdateStatusRequest,
    AdminCommentListItem,
    AdminCommentListResponse,
    AdminCommentUpdateRiskRequest,
)
from app.services.admin_auth_service import login_admin
from app.services.user_service import get_user_by_id, list_users_for_admin
from app.services.salary_service import (
    list_all_for_admin,
    delete_for_admin,
    update_risk_for_admin,
    record_to_response as salary_record_to_response,
)
from app.services.statistics_service import get_admin_dashboard_stats
from app.services.post_service import (
    list_posts_for_admin,
    get_by_id_for_admin as get_post_by_id_for_admin,
    update_post_status_for_admin,
    delete_post_for_admin,
)
from app.services.comment_service import (
    list_comments_for_admin,
    update_comment_risk_for_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/auth/login", response_model=AdminTokenResponse)
async def admin_login(
    body: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """管理员登录，返回 JWT 和 CSRF token

    SECURITY: JWT token 设置在 httpOnly cookie 中，防止 XSS 窃取
    CSRF token 在响应体中返回，需要前端存储并在后续请求中携带
    """
    tokens = await login_admin(db, body.username, body.password)
    if not tokens:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    jwt_token, csrf_token = tokens

    # 创建响应对象
    response = JSONResponse(
        content={
            "access_token": jwt_token,
            "token_type": "bearer",
            "csrf_token": csrf_token
        }
    )

    # SECURITY: 设置 httpOnly cookie，防止 JavaScript 访问 token
    # SameSite=strict 防止 CSRF 攻击
    # Secure 确保仅通过 HTTPS 传输
    response.set_cookie(
        key="payday_admin_token",
        value=jwt_token,
        httponly=True,  # 防止 JavaScript 访问
        samesite="strict",  # 防止 CSRF
        secure=False,  # 开发环境为 False，生产环境应为 True
        max_age=3600,  # 1小时
        path="/",
    )

    return response


@router.post("/auth/refresh")
async def admin_refresh_token(
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    刷新管理员 Access Token

    Args:
        refresh_token: 刷新令牌

    Returns:
        新的 access_token 和 csrf_token，以及新的 refresh_token

    SECURITY:
    - 从 refresh token 中解析 admin ID
    - 验证 token 有效性和未撤销
    - 生成新的 token 对并撤销旧的 refresh token
    """
    from app.services.admin_auth_service import refresh_admin_token

    result = await refresh_admin_token(db, refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="无效或过期的 Refresh Token")

    new_access_token, new_csrf_token, new_refresh_token = result

    # 创建响应对象
    response = JSONResponse(
        content={
            "access_token": new_access_token,
            "csrf_token": new_csrf_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    )

    # SECURITY: 更新 httpOnly cookie
    response.set_cookie(
        key="payday_admin_token",
        value=new_access_token,
        httponly=True,
        samesite="strict",
        secure=False,  # 开发环境为 False，生产环境应为 True
        max_age=3600,  # 1小时
        path="/",
    )

    return response


@router.get("/users", response_model=dict)
async def admin_user_list(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: Optional[str] = Query(None, description="匿名昵称关键词"),
    status: Optional[str] = Query(None, description="状态：normal / disabled"),
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端用户列表（分页；可选按昵称关键词、状态筛选）"""
    users, total = await list_users_for_admin(
        db, limit=limit, offset=offset, keyword=keyword, status=status
    )
    items = [
        AdminUserListItem(
            id=u.id,
            openid=u.openid,
            anonymous_name=u.anonymous_name,
            status=u.status.value if hasattr(u.status, "value") else str(u.status),
            created_at=u.created_at,
        )
        for u in users
    ]
    return {"items": items, "total": total}


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def admin_user_detail(
    user_id: str,
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端用户详情"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    status_val = user.status.value if hasattr(user.status, "value") else str(user.status)
    return AdminUserDetail(
        id=user.id,
        openid=user.openid,
        anonymous_name=user.anonymous_name,
        status=status_val,
        created_at=user.created_at,
        unionid=user.unionid,
        avatar=user.avatar,
        bio=user.bio,
        follower_count=user.follower_count,
        following_count=user.following_count,
        post_count=user.post_count,
        allow_follow=user.allow_follow,
        allow_comment=user.allow_comment,
        updated_at=user.updated_at,
    )


@router.get("/salary-records", response_model=dict)
async def admin_salary_list(
    user_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端工资记录列表（可选按 user_id 过滤）"""
    items, total = await list_all_for_admin(db, user_id=user_id, limit=limit, offset=offset)
    return {"items": [AdminSalaryRecordItem(**x) for x in items], "total": total}


@router.delete("/salary-records/{record_id}", status_code=204)
async def admin_salary_delete(
    record_id: str,
    _admin: AdminUser = Depends(get_current_admin),
    _perm: bool = Depends(require_permission("admin")),  # 需要admin或更高级别权限
    __: bool = Depends(verify_csrf_token),
    db: AsyncSession = Depends(get_db),
):
    """管理端删除工资记录（需要 CSRF token）"""
    ok = await delete_for_admin(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")


@router.put("/salary-records/{record_id}/risk", response_model=AdminSalaryRecordItem)
async def admin_salary_update_risk(
    record_id: str,
    body: AdminSalaryRecordUpdateRiskRequest,
    _admin: AdminUser = Depends(get_current_admin),
    _perm: bool = Depends(require_permission("admin")),  # 需要admin或更高级别权限
    __: bool = Depends(verify_csrf_token),
    db: AsyncSession = Depends(get_db),
):
    """管理端人工审核工资记录（通过/拒绝）（需要 CSRF token）"""
    record = await update_risk_for_admin(db, record_id, body.risk_status)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return salary_record_to_response(record)


@router.get("/statistics", response_model=AdminStatisticsResponse)
async def admin_statistics(
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端仪表盘统计"""
    stats = await get_admin_dashboard_stats(db)
    return AdminStatisticsResponse(**stats)


# ----- 帖子管理（Sprint 2.4） -----


@router.get("/posts", response_model=AdminPostListResponse)
async def admin_post_list(
    status: Optional[str] = Query(None, description="normal | hidden | deleted"),
    risk_status: Optional[str] = Query(None, description="pending | approved | rejected"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端帖子列表（分页；可选按 status、risk_status 筛选；风控待审用 risk_status=pending）"""
    posts, total = await list_posts_for_admin(
        db, status=status, risk_status=risk_status, limit=limit, offset=offset
    )
    items = [
        AdminPostListItem(
            id=p.id,
            user_id=p.user_id,
            anonymous_name=p.anonymous_name or "",
            content=p.content or "",
            images=p.images,
            type=p.type.value if hasattr(p.type, "value") else str(p.type),
            view_count=p.view_count or 0,
            like_count=p.like_count or 0,
            comment_count=p.comment_count or 0,
            status=p.status.value if hasattr(p.status, "value") else str(p.status),
            risk_status=p.risk_status.value if hasattr(p.risk_status, "value") else str(p.risk_status),
            risk_score=p.risk_score,
            risk_reason=p.risk_reason,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in posts
    ]
    return AdminPostListResponse(items=items, total=total)


@router.get("/posts/{post_id}", response_model=AdminPostListItem)
async def admin_post_detail(
    post_id: str,
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端帖子详情"""
    post = await get_post_by_id_for_admin(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return AdminPostListItem(
        id=post.id,
        user_id=post.user_id,
        anonymous_name=post.anonymous_name or "",
        content=post.content or "",
        images=post.images,
        type=post.type.value if hasattr(post.type, "value") else str(post.type),
        view_count=post.view_count or 0,
        like_count=post.like_count or 0,
        comment_count=post.comment_count or 0,
        status=post.status.value if hasattr(post.status, "value") else str(post.status),
        risk_status=post.risk_status.value if hasattr(post.risk_status, "value") else str(post.risk_status),
        risk_score=post.risk_score,
        risk_reason=post.risk_reason,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.put("/posts/{post_id}/status")
async def admin_post_update_status(
    post_id: str,
    body: AdminPostUpdateStatusRequest,
    _admin: AdminUser = Depends(get_current_admin),
    _perm: bool = Depends(require_permission("admin")),  # 需要admin或更高级别权限
    __: bool = Depends(verify_csrf_token),
    db: AsyncSession = Depends(get_db),
):
    """管理端更新帖子状态（隐藏/恢复）或人工审核（通过/拒绝）（需要 CSRF token）"""
    post = await update_post_status_for_admin(
        db,
        post_id,
        status=body.status,
        risk_status=body.risk_status,
        risk_reason=body.risk_reason,
    )
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"ok": True, "id": post_id}


@router.delete("/posts/{post_id}", status_code=204)
async def admin_post_delete(
    post_id: str,
    _admin: AdminUser = Depends(get_current_admin),
    _perm: bool = Depends(require_permission("admin")),  # 需要admin或更高级别权限
    __: bool = Depends(verify_csrf_token),
    db: AsyncSession = Depends(get_db),
):
    """管理端软删帖子（status=deleted）（需要 CSRF token）"""
    ok = await delete_post_for_admin(db, post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="帖子不存在")


# ----- 评论管理（Sprint 2.4） -----


@router.get("/comments", response_model=AdminCommentListResponse)
async def admin_comment_list(
    post_id: Optional[str] = Query(None),
    risk_status: Optional[str] = Query(None, description="pending | approved | rejected"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _perm: bool = Depends(require_permission("readonly")),  # 需要readonly或更高级别权限
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理端评论列表（可选按 post_id、risk_status 筛选；风控待审用 risk_status=pending）"""
    comments, total = await list_comments_for_admin(
        db, post_id=post_id, risk_status=risk_status, limit=limit, offset=offset
    )
    items = [
        AdminCommentListItem(
            id=c.id,
            post_id=c.post_id,
            user_id=c.user_id,
            anonymous_name=c.anonymous_name or "",
            content=c.content or "",
            parent_id=c.parent_id,
            like_count=c.like_count or 0,
            risk_status=c.risk_status.value if hasattr(c.risk_status, "value") else str(c.risk_status),
            created_at=c.created_at,
        )
        for c in comments
    ]
    return AdminCommentListResponse(items=items, total=total)


@router.put("/comments/{comment_id}/risk")
async def admin_comment_update_risk(
    comment_id: str,
    body: AdminCommentUpdateRiskRequest,
    _admin: AdminUser = Depends(get_current_admin),
    _perm: bool = Depends(require_permission("admin")),  # 需要admin或更高级别权限
    __: bool = Depends(verify_csrf_token),
    db: AsyncSession = Depends(get_db),
):
    """管理端人工审核评论（通过/拒绝）（需要 CSRF token）"""
    comment = await update_comment_risk_for_admin(
        db, comment_id, risk_status=body.risk_status, risk_reason=body.risk_reason
    )
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return {"ok": True, "id": comment_id}
