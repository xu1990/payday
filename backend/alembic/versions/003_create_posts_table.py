"""create posts table

Revision ID: 003
Revises: 002
Create Date: 2025-02-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("anonymous_name", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("complaint", "sharing", "question", name="post_type_enum"),
            nullable=False,
            server_default="complaint",
        ),
        sa.Column("salary_range", sa.String(20), nullable=True),
        sa.Column("industry", sa.String(50), nullable=True),
        sa.Column("city", sa.String(50), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("normal", "hidden", "deleted", name="post_status_enum"),
            nullable=False,
            server_default="normal",
        ),
        sa.Column(
            "risk_status",
            sa.Enum("pending", "approved", "rejected", name="risk_status_enum"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"])
    op.create_index(
        "idx_posts_hot",
        "posts",
        ["type", "status", "risk_status", "like_count", "created_at"],
    )
    op.create_index("idx_posts_user", "posts", ["user_id", "status", "created_at"])
    op.create_index("idx_posts_tag", "posts", ["type", "city", "industry", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_posts_tag", table_name="posts")
    op.drop_index("idx_posts_user", table_name="posts")
    op.drop_index("idx_posts_hot", table_name="posts")
    op.drop_index("ix_posts_user_id", table_name="posts")
    op.drop_table("posts")
