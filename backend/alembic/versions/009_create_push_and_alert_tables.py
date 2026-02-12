"""create push_notifications and risk_alerts tables

Revision ID: 009
Revises: 008
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


def upgrade():
    # 创建push_notifications表
    op.create_table(
        'push_notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, comment='接收用户'),
        sa.Column('title', sa.String(100), nullable=False, comment='推送标题'),
        sa.Column('content', sa.Text(), nullable=True, comment='推送内容'),
        sa.Column('type', sa.String(20), nullable=False, comment='推送类型'),
        sa.Column('target_type', sa.String(20), nullable=True, comment='跳转类型'),
        sa.Column('target_id', sa.String(36), nullable=True, comment='跳转目标ID'),
        sa.Column('is_sent', sa.Boolean(), default=False, nullable=False, comment='是否已发送'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='发送时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # 创建risk_alerts表
    op.create_table(
        'risk_alerts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, comment='关联用户'),
        sa.Column('target_type', sa.String(20), nullable=False, comment='目标类型'),
        sa.Column('target_id', sa.String(36), nullable=True, comment='目标ID'),
        sa.Column('risk_score', sa.Integer(), nullable=False, comment='风险评分'),
        sa.Column('risk_reason', sa.String(200), nullable=True, comment='风险原因'),
        sa.Column('is_handled', sa.Boolean(), default=False, nullable=False, comment='是否已处理'),
        sa.Column('handled_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True, comment='处理人'),
        sa.Column('handled_at', sa.DateTime(), nullable=True, comment='处理时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )


def downgrade():
    # 删除表
    op.drop_table('push_notifications')
    op.drop_table('risk_alerts')
