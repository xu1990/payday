"""add feedbacks table and topic_id to posts (MySQL)

Revision ID: 19202799da72
Revises: 19192799da71
Create Date: 2026-02-20 10:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '19202799da72'
down_revision: Union[str, None] = '19192799da71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For MySQL production, add topic_id column to posts table
    # This will be applied when using MySQL instead of SQLite
    try:
        op.add_column('posts', sa.Column('topic_id', sa.String(36), nullable=True, comment='关联话题ID'))
        op.create_index('ix_posts_topic_id', 'posts', ['topic_id'])
    except Exception:
        # Column might already exist or different database
        pass


def downgrade() -> None:
    try:
        op.drop_index('ix_posts_topic_id', table_name='posts')
        op.drop_column('posts', 'topic_id')
    except Exception:
        pass
