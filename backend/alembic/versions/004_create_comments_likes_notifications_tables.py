"""create comments, likes, notifications tables

Revision ID: 004
Revises: 003
Create Date: 2025-02-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 评论表（复用 risk_status_enum）
    op.create_table(
        "comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("post_id", sa.String(36), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("anonymous_name", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "risk_status",
            sa.Enum("pending", "approved", "rejected", name="risk_status_enum"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_parent_id", "comments", ["parent_id"])
    op.create_index("idx_comments_hot", "comments", ["post_id", "created_at"])
    op.create_index("idx_comments_user", "comments", ["user_id", "created_at"])

    # 点赞表（MySQL ENUM 在列定义中）
    op.create_table(
        "likes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "target_type",
            sa.Enum("post", "comment", name="like_target_type_enum"),
            nullable=False,
        ),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "target_type", "target_id", name="uq_like_user_target"),
    )
    op.create_index("ix_likes_user_id", "likes", ["user_id"])
    op.create_index("ix_likes_target", "likes", ["target_type", "target_id"])

    # 通知表（MySQL ENUM 在列定义中）
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "type",
            sa.Enum("comment", "reply", "like", "system", name="notification_type_enum"),
            nullable=False,
        ),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("related_id", sa.String(36), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_likes_target", table_name="likes")
    op.drop_index("ix_likes_user_id", table_name="likes")
    op.drop_table("likes")

    op.drop_index("idx_comments_user", table_name="comments")
    op.drop_index("idx_comments_hot", table_name="comments")
    op.drop_index("ix_comments_parent_id", table_name="comments")
    op.drop_index("ix_comments_user_id", table_name="comments")
    op.drop_index("ix_comments_post_id", table_name="comments")
    op.drop_table("comments")
