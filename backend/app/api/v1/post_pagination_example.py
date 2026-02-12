"""
游标分页 API 示例 - 技术方案 4.1.1
展示如何将传统 OFFSET 分页改造为游标分页
"""
from typing import Literal, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.post import Post
from app.schemas.post import PostResponse
from app.utils.pagination import CursorPaginator

router = APIRouter(prefix="/posts_v2", tags=["posts_v2"])


@router.get("", response_model=dict)
async def post_list_cursor(
    sort: Literal["hot", "latest"] = Query("latest", description="hot=热门 latest=最新"),
    cursor: Optional[str] = Query(None, description="游标（第一页不传）"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    帖子列表（游标分页）

    技术方案 4.1.1 - 避免深度分页性能问题
    使用基于 ID 的游标分页替代 OFFSET

    请求参数:
        sort: 排序方式 (hot/latest)
        cursor: 上一页返回的 next_cursor
        limit: 每页数量（默认20）

    返回:
        {
            "items": [...],
            "next_cursor": "...",  # 下一页游标
            "has_more": true/false
        }
    """
    # 构建排序规则
    # 热门帖子按: like_count DESC, comment_count DESC, view_count DESC, id DESC
    # 最新帖子按: created_at DESC, id DESC
    from sqlalchemy import desc

    if sort == "hot":
        order_by = [
            desc(Post.like_count),
            desc(Post.comment_count),
            desc(Post.view_count),
            desc(Post.id),
        ]
    else:  # latest
        order_by = [
            desc(Post.created_at),
            desc(Post.id),
        ]

    # 创建游标分页器
    paginator = CursorPaginator(
        model=Post,
        order_by=order_by,
        filter_expr=(Post.status == "normal"),  # 只返回正常状态的帖子
    )

    # 执行分页查询
    result = await paginator.paginate(
        db,
        limit=limit,
        cursor=cursor,
        with_count=False,  # 游标分页不需要返回总数
    )

    # 转换为响应格式
    return {
        "items": [PostResponse.model_validate(p) for p in result.items],
        "next_cursor": result.next_cursor,
        "has_more": result.has_more,
    }


@router.get("/search", response_model=dict)
async def post_search_cursor(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    tags: Optional[str] = Query(None, description="标签搜索，逗号分隔"),
    sort: Literal["hot", "latest"] = Query("latest", description="排序方式"),
    cursor: Optional[str] = Query(None, description="游标"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = AsyncSession = Depends(get_db),
):
    """
    搜索帖子（游标分页）

    演示带筛选条件的游标分页
    """
    from sqlalchemy import or_, desc

    # 构建筛选条件
    filters = [Post.status == "normal"]

    if keyword:
        # 关键词搜索（标题或内容）
        keyword_filter = or_(
            Post.content.ilike(f"%{keyword}%"),
            Post.content.ilike(f"%{keyword}%"),
        )
        filters.append(keyword_filter)

    if tags:
        # 标签筛选 - JSON_CONTAINS 查询包含任一指定标签的帖子
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            # 构建 JSON_CONTAINS 条件：tags 字段包含任一标签
            # MySQL: JSON_CONTAINS(tags, '"tag1"') OR JSON_CONTAINS(tags, '"tag2"')
            tag_filters = []
            for tag in tag_list:
                # JSON_CONTAINS 第二个参数需要是 JSON 格式的字符串
                tag_filters.append(Post.tags.contains(tag))
            # 任一标签匹配即可
            from sqlalchemy import or_
            filters.append(or_(*tag_filters))

    # 组合所有筛选条件
    from sqlalchemy import and_
    filter_expr = and_(*filters) if filters else None

    # 排序规则
    if sort == "hot":
        order_by = [
            desc(Post.like_count),
            desc(Post.id),
        ]
    else:
        order_by = [
            desc(Post.created_at),
            desc(Post.id),
        ]

    # 创建分页器
    paginator = CursorPaginator(
        model=Post,
        order_by=order_by,
        filter_expr=filter_expr,
    )

    # 执行分页
    result = await paginator.paginate(
        db,
        limit=limit,
        cursor=cursor,
        with_count=False,
    )

    return {
        "items": [PostResponse.model_validate(p) for p in result.items],
        "next_cursor": result.next_cursor,
        "has_more": result.has_more,
    }


# ============================================================
# 迁移指南：将现有 API 改造为游标分页
# ============================================================

"""
步骤 1: 将传统 OFFSET 分页改造为游标分页

改造前（使用 OFFSET）:
--------------------------
@router.get("/posts")
async def get_posts(offset: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    query = select(Post).order_by(Post.created_at.desc())
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    posts = result.scalars().all()

    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar()

    return {"items": posts, "total": total, "offset": offset + limit}


改造后（使用游标分页）:
--------------------------
from app.utils.pagination import CursorPaginator

@router.get("/posts")
async def get_posts(cursor: str = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    paginator = CursorPaginator(
        model=Post,
        order_by=[Post.created_at.desc(), Post.id.desc()],
    )

    result = await paginator.paginate(db, limit=limit, cursor=cursor)

    return {
        "items": result.items,
        "next_cursor": result.next_cursor,
        "has_more": result.has_more,
    }


步骤 2: 前端适配（小程序）
--------------------------

改造前:
-------
const res = await getPosts({ offset: 0, limit: 20 })
setPosts(res.items)
// 下一页
const nextRes = await getPosts({ offset: 20, limit: 20 })


改造后:
-------
const res = await getPosts({ limit: 20 })
setPosts(res.items)
setNextCursor(res.next_cursor)
// 下一页
const nextRes = await getPosts({ limit: 20, cursor: nextCursor })


步骤 3: 性能对比
------------------

OFFSET 分页（深度分页时）:
- SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 10000;
- 需要扫描前 10000 条记录
- 随着页码增加，性能下降

游标分页（深度分页时）:
- SELECT * FROM posts
  WHERE (created_at < '2024-01-01' OR (created_at = '2024-01-01' AND id < 12345))
  ORDER BY created_at DESC, id DESC
  LIMIT 20
- 使用索引直接定位
- 性能稳定


步骤 4: 数据库索引优化
------------------

确保创建必要的复合索引:

CREATE INDEX idx_posts_created_id ON posts (created_at DESC, id DESC);
CREATE INDEX idx_posts_hot ON posts (like_count DESC, comment_count DESC, view_count DESC, id DESC);


注意事项:
---------

1. 游标分页不适合跳页场景（如跳到第10页）
   - 如果需要跳页功能，保留 OFFSET 分页作为备选

2. 排序字段必须包含唯一字段（通常是 id）
   - 确保游标是唯一的，避免重复或遗漏

3. 游标是 base64 编码的 JSON
   - 不要尝试解析游标内容
   - 直接透传给下一页

4. 第一页请求不传 cursor
   - 后续页传入上一页返回的 next_cursor
"""
