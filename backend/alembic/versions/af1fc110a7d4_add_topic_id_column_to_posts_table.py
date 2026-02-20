"""add topic_id column to posts table

Revision ID: af1fc110a7d4
Revises: 19202799da72
Create Date: 2026-02-20 14:22:33.965281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af1fc110a7d4'
down_revision: Union[str, None] = '19202799da72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only add topic_id column - SQLite has limited ALTER COLUMN support
    op.add_column('posts', sa.Column('topic_id', sa.String(length=36), nullable=True, comment='关联话题ID'))
    op.create_index(op.f('ix_posts_topic_id'), 'posts', ['topic_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_posts_topic_id'), table_name='posts')
    op.drop_column('posts', 'topic_id')
