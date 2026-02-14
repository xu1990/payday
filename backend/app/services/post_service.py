"""
帖子服务 - 发帖、列表（热门/最新）、详情；管理端列表/状态/删除；与技术方案 2.2、3.3.1 一致
"""
from typing import List, Literal, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.schemas.post import PostCreate
from app.core.cache import PostCacheService
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.sanitize import sanitize_html


async def create(
    db: AsyncSession,
    user_id: str,
    data: PostCreate,
    *,
    anonymous_name: str,
) -> Post:
    # 净化用户输入的内容，防止 XSS 攻击
    sanitized_content = sanitize_html(data.content)

    post = Post(
        user_id=user_id,
        anonymous_name=anonymous_name,
        content=sanitized_content,
        images=data.images,
        tags=data.tags,
        type=data.type,
        salary_range=data.salary_range,
        industry=data.industry,
        city=data.city,
        status="normal",
        risk_status="pending",
    )
    try:
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post
    except SQLAlchemyError:
        await db.rollback()
        raise


async def get_by_id(
    db: AsyncSession,
    post_id: str,
    only_approved: bool = True,
    increment_view: bool = True,
) -> Optional[Post]:
    """获取帖子详情，可选是否增加浏览量（从缓存计数）"""
    q = select(Post).where(Post.id == post_id, Post.status == "normal")
    if only_approved:
        q = q.where(Post.risk_status == "approved")
    result = await db.execute(q)
    post = result.scalar_one_or_none()

    # 增加浏览计数到 Redis（异步，不阻塞响应）
    if post and increment_view:
        try:
            view_count = await PostCacheService.increment_view_count(post_id)
            post.view_count = view_count
        except Exception as e:
            # Redis 故障时记录日志但不影响主流程
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to increment view count for post {post_id}: {e}")

    return post


async def list_posts(
    db: AsyncSession,
    sort: Literal["hot", "latest"] = "latest",
    limit: int = 20,
    offset: int = 0,
) -> List[Post]:
    """帖子列表，热门从缓存获取，最新从数据库查询"""
    if sort == "hot":
        # 尝试从 Redis 获取热门帖子 ID 列表
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            hot_post_ids = await PostCacheService.get_hot_posts(date, 0, limit - 1)
            if hot_post_ids:
                # 按 ID 列表查询完整数据
                posts = await get_posts_by_ids(db, hot_post_ids)
                # 分页处理（offset 在缓存结果上处理）
                return posts[offset:] if offset < len(posts) else []
        except Exception:
            # Redis 故障时降级到数据库查询
            pass

    # 最新或降级查询：从数据库获取
    q = (
        select(Post)
        .where(Post.status == "normal", Post.risk_status == "approved")
        .limit(limit)
        .offset(offset)
    )
    if sort == "hot":
        q = q.order_by(Post.like_count.desc(), Post.created_at.desc())
    else:
        q = q.order_by(Post.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_posts_by_ids(db: AsyncSession, post_ids: List[str]) -> List[Post]:
    """根据 ID 列表批量查询帖子（保持顺序）"""
    if not post_ids:
        return []
    # 查询所有帖子
    result = await db.execute(
        select(Post).where(
            Post.id.in_(post_ids),
            Post.status == "normal",
            Post.risk_status == "approved"
        )
    )
    posts_by_id = {p.id: p for p in result.scalars().all()}
    # 按 ID 列表顺序返回
    return [posts_by_id[pid] for pid in post_ids if pid in posts_by_id]


async def update_hot_posts_ranking(db: AsyncSession) -> None:
    """更新热门帖子排名（定时任务调用）
    按分数 = like_count * 2 + comment_count 计算热度
    """
    # 获取近24小时的帖子
    from datetime import timedelta
    since = datetime.now() - timedelta(days=1)
    result = await db.execute(
        select(Post)
        .where(
            Post.status == "normal",
            Post.risk_status == "approved",
            Post.created_at >= since
        )
        .order_by(Post.like_count.desc())
        .limit(100)
    )
    posts = result.scalars().all()

    # 更新到 Redis ZSet
    date = datetime.now().strftime("%Y-%m-%d")
    for post in posts:
        # 热度分数计算：点赞数 * 2 + 评论数
        score = post.like_count * 2 + post.comment_count
        try:
            await PostCacheService.add_to_hot_posts(post.id, score, date)
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to add post {post.id} to hot posts: {e}")


async def list_posts_for_admin(
    db: AsyncSession,
    status: Optional[str] = None,
    risk_status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Post], int]:
    """管理端帖子列表：可选按 status、risk_status 筛选，返回列表与总数"""
    base = select(Post)
    count_base = select(func.count()).select_from(Post)
    if status:
        base = base.where(Post.status == status)
        count_base = count_base.where(Post.status == status)
    if risk_status:
        base = base.where(Post.risk_status == risk_status)
        count_base = count_base.where(Post.risk_status == risk_status)
    total = (await db.execute(count_base)).scalar() or 0
    q = base.order_by(Post.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_by_id_for_admin(db: AsyncSession, post_id: str) -> Optional[Post]:
    """管理端取帖子详情（不限制 status/risk_status）"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


async def update_post_status_for_admin(
    db: AsyncSession,
    post_id: str,
    *,
    status: Optional[str] = None,
    risk_status: Optional[str] = None,
    risk_reason: Optional[str] = None,
) -> Optional[Post]:
    """管理端更新帖子状态（status 隐藏/恢复/删除）或风控人工通过/拒绝"""
    post = await get_by_id_for_admin(db, post_id)
    if not post:
        raise NotFoundException("帖子不存在")
    if status is not None:
        post.status = status
    if risk_status is not None:
        post.risk_status = risk_status
    if risk_reason is not None:
        post.risk_reason = risk_reason
    try:
        await db.commit()
        await db.refresh(post)
        return post
    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete_post_for_admin(db: AsyncSession, post_id: str) -> bool:
    """管理端删除帖子（软删：status=deleted）"""
    post = await get_by_id_for_admin(db, post_id)
    if not post:
        return False
    post.status = "deleted"
    try:
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        raise


async def search_posts(
    db: AsyncSession,
    keyword: Optional[str] = None,
    tags: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    salary_range: Optional[str] = None,
    sort: Literal["hot", "latest"] = "latest",
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Post], int]:
    """搜索帖子：按关键词、标签、用户、行业、城市、工资区间筛选"""
    # 构建基础查询
    query = select(Post).where(
        Post.status == "normal",
        Post.risk_status == "approved"
    )

    # 按关键词搜索
    # SECURITY: 使用 SQLAlchemy 参数绑定防止 SQL 注入
    if keyword:
        # 验证输入是字符串且长度合理
        if not isinstance(keyword, str):
            raise ValidationException("Search keyword must be a string")
        if len(keyword) > 100:
            raise ValidationException("Search keyword too long (max 100 characters)")

        # 移除控制字符，防止注入攻击
        keyword = ''.join(char for char in keyword if ord(char) >= 32 or char in '\n\t\r')

        # 使用 SQLAlchemy 的 bindparam 自动转义，防止 SQL 注入
        # SQLAlchemy 会正确处理参数绑定，无需手动转义
        search_pattern = f"%{keyword}%"
        query = query.where(Post.content.ilike(search_pattern))

    # 按标签搜索（JSON查询）
    if tags:
        # SECURITY: 验证并清理标签，防止注入
        import re
        valid_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                continue
            if len(tag) > 20:
                continue
            # 标签验证：仅允许字母数字、中文、空格、连字符、下划线
            if not re.match(r'^[\\w\u4e00-\\u9fff\\s\\-_]+$', tag):
                continue
            valid_tags.append(tag)

        # 使用验证后的标签列表进行JSON包含查询
        # SECURITY: 使用参数化查询防止SQL注入
        if valid_tags:
            from sqlalchemy import or_, text, bindparam

            tag_conditions = []
            for tag in valid_tags:
                # SECURITY: 创建命名参数并安全绑定
                # JSON_CONTAINS 是 MySQL 的安全函数，使用参数化查询
                param_name = f'tag_{len(tag_conditions)}'
                tag_value = json.dumps([tag])  # 使用 json.dumps 确保安全转义
                tag_conditions.append(
                    text(f"JSON_CONTAINS(tags, :{param_name})").bindparams(
                        bindparam(param_name, tag_value)
                    )
                )

            if tag_conditions:
                query = query.where(or_(*tag_conditions))

    # 按用户搜索
    if user_id:
        query = query.where(Post.user_id == user_id)

    # 按行业筛选
    if industry:
        query = query.where(Post.industry == industry)

    # 按城市筛选
    if city:
        query = query.where(Post.city == city)

    # 按工资区间筛选
    if salary_range:
        query = query.where(Post.salary_range == salary_range)

    # 排序
    if sort == "hot":
        query = query.order_by(Post.like_count.desc(), Post.created_at.desc())
    else:  # latest
        query = query.order_by(Post.created_at.desc())

    # 先获取总数
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 应用分页和限制
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    posts = result.scalars().all()

    return list(posts), total
