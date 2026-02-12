"""Add performance indexes for better query performance

Revision ID: 010
Revises: 009
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'


def upgrade():
    # follows表索引 - 用于快速查询用户的关注/粉丝关系
    op.create_index(
        "idx_follows_follower",
        "follows",
        ["follower_id"],
        unique=False,
    )
    op.create_index(
        "idx_follows_following",
        "follows",
        ["following_id"],
        unique=False,
    )

    # likes表索引 - 用于快速查询点赞记录
    op.create_index(
        "idx_likes_user_target",
        "likes",
        ["user_id", "target_id", "target_type"],
        unique=False,
    )

    # comments表索引 - 用于快速查询评论
    op.create_index(
        "idx_comments_user_post",
        "comments",
        ["user_id", "post_id"],
        unique=False,
    )
    op.create_index(
        "idx_comments_post_parent",
        "comments",
        ["post_id"],
        unique=False,
    )

    # salary_records表索引 - 用于按日期查询工资记录
    op.create_index(
        "idx_salary_records_user_payday",
        "salary_records",
        ["user_id", "payday_date"],
        unique=False,
    )

    # posts表已存在索引，这里不再重复创建


def downgrade():
    # 删除所有添加的索引
    op.drop_index("idx_follows_follower", table_name="follows")
    op.drop_index("idx_follows_following", table_name="follows")
    op.drop_index("idx_likes_user_target", table_name="likes")
    op.drop_index("idx_comments_user_post", table_name="comments")
    op.drop_index("idx_comments_post_parent", table_name="comments")
    op.drop_index("idx_salary_records_user_payday", table_name="salary_records")
