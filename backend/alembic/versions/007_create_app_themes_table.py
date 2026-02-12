"""create app_themes table

Revision ID: 008
Revises: 007
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = '008'
down_revision = '007'


def upgrade():
    # 创建app_themes表
    op.create_table(
        'app_themes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, comment='主题名称'),
        sa.Column('code', sa.String(50), nullable=False, unique=True, comment='主题代码'),
        sa.Column('preview_image', sa.String(500), nullable=True, comment='预览图'),
        sa.Column('config', sa.Text(), nullable=True, comment='主题配置（JSON）'),
        sa.Column('is_premium', sa.Boolean(), default=False, nullable=False, comment='是否会员专属'),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False, comment='是否启用'),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False, comment='排序'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )


def downgrade():
    # 删除app_themes表
    op.drop_table('app_themes')
