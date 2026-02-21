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
    # Only add topic_id column if it doesn't exist (may already exist from 19202799da72)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if topic_id already exists
    columns = [col['name'] for col in inspector.get_columns('posts')]
    if 'topic_id' not in columns:
        op.add_column('posts', sa.Column('topic_id', sa.String(length=36), nullable=True, comment='关联话题ID'))

    # Check if index exists before creating
    indexes = [idx['name'] for idx in inspector.get_indexes('posts')]
    if 'ix_posts_topic_id' not in indexes:
        op.create_index(op.f('ix_posts_topic_id'), 'posts', ['topic_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_posts_topic_id'), table_name='posts')
    op.drop_column('posts', 'topic_id')
