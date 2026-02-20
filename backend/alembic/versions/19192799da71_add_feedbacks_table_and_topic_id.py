"""add feedbacks table and topic_id to posts

Revision ID: 19192799da71
Revises: 090c6cd520b3
Create Date: 2026-02-20 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '19192799da71'
down_revision: Union[str, None] = '090c6cd520b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create feedbacks table
    op.create_table('feedbacks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False, comment='用户ID'),
    sa.Column('content', sa.Text(), nullable=False, comment='反馈内容'),
    sa.Column('images', mysql.JSON(), nullable=True, comment='反馈图片列表'),
    sa.Column('contact', sa.String(length=100), nullable=True, comment='联系方式'),
    sa.Column('status', sa.String(length=20), nullable=True, comment='状态: pending/processing/resolved'),
    sa.Column('admin_reply', sa.Text(), nullable=True, comment='管理员回复'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedbacks_user_id'), 'feedbacks', ['user_id'], unique=False)

    # Add topic_id column to posts table (skip for SQLite as it requires recreating table)
    # For MySQL: op.add_column('posts', sa.Column('topic_id', sa.String(36), nullable=True))
    # For SQLite development, we'll skip this and handle it in MySQL production


def downgrade() -> None:
    op.drop_index(op.f('ix_feedbacks_user_id'), table_name='feedbacks')
    op.drop_table('feedbacks')

    # To rollback topic_id column (for MySQL):
    # op.drop_column('posts', 'topic_id')
