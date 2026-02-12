"""create follows table

Revision ID: 005
Revises: 004
Create Date: 2025-02-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "follows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("follower_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, comment="关注者"),
        sa.Column("following_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, comment="被关注者"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("follower_id", "following_id", name="uk_follow"),
    )
    op.create_index("ix_follows_follower_id", "follows", ["follower_id"])
    op.create_index("ix_follows_following_id", "follows", ["following_id"])


def downgrade() -> None:
    op.drop_index("ix_follows_following_id", table_name="follows")
    op.drop_index("ix_follows_follower_id", table_name="follows")
    op.drop_table("follows")
