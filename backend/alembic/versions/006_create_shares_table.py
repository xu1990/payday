"""create shares table

Revision ID: 006
Revises: 005
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


def upgrade():
    # 创建shares表
    op.create_table(
        'shares',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('target_type', sa.String(20), nullable=False, comment='分享目标类型：post/salary/poster'),
        sa.Column('target_id', sa.String(36), nullable=True, comment='分享目标ID（帖子ID/工资记录ID等）'),
        sa.Column('share_channel', sa.String(20), nullable=False, comment='分享渠道：wechat_friend/wechat_moments'),
        sa.Column('share_status', sa.String(20), default='pending', nullable=False, comment='分享状态：pending/success/failed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    )


def downgrade():
    # 删除shares表
    op.drop_table('shares')
