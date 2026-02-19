"""create topics table

Revision ID: 006b_create_topics_table
Revises: 006
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = '006b_create_topics_table'
down_revision = '006'


def upgrade():
    # 创建topics表
    op.create_table(
        'topics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, comment='话题名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='话题描述'),
        sa.Column('cover_image', sa.String(500), nullable=True, comment='封面图片URL'),
        sa.Column('post_count', sa.Integer(), default=0, nullable=False, comment='关联帖子数'),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False, comment='是否启用'),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False, comment='排序权重'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )


def downgrade():
    # 删除topics表
    op.drop_table('topics')
