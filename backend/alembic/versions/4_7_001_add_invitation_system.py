"""add invitation system - Sprint 4.7

Revision ID: 4_7_001
Revises: c1_expense_remove_salt
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4_7_001'
down_revision = 'c1_expense_remove_salt'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 给users表添加邀请码字段
    op.add_column('users', sa.Column('invite_code', sa.String(12), nullable=True))
    op.create_index('ix_users_invite_code', 'users', ['invite_code'], unique=True)
    op.add_column('users', sa.Column('invited_by', sa.String(36), nullable=True))
    op.create_index('ix_users_invited_by', 'users', ['invited_by'])

    # 注意：SQLite不支持ALTER TABLE添加外键约束
    # 外键关系由ORM模型定义，应用层维护

    # 2. 创建user_invitations表
    op.create_table(
        'user_invitations',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('inviter_id', sa.String(36), nullable=False, comment='邀请者ID'),
        sa.Column('invitee_id', sa.String(36), nullable=False, comment='被邀请者ID'),
        sa.Column('invite_code_used', sa.String(12), nullable=False, comment='使用的邀请码'),
        sa.Column('inviter_points_rewarded', sa.String(36), nullable=True, comment='邀请者积分流水ID'),
        sa.Column('invitee_points_rewarded', sa.String(36), nullable=True, comment='被邀请者积分流水ID'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),

        comment='用户邀请关系记录表'
    )

    # 创建索引
    op.create_index('ix_user_invitations_inviter_id', 'user_invitations', ['inviter_id'])
    op.create_index('ix_user_invitations_invitee_id', 'user_invitations', ['invitee_id'])
    op.create_index('ix_user_invitations_inviter_invitee', 'user_invitations', ['inviter_id', 'invitee_id'])

    # 创建唯一约束
    op.create_unique_constraint('uq_user_invitations_invitee', 'user_invitations', ['invitee_id'])


def downgrade():
    # 删除唯一约束
    op.drop_constraint('uq_user_invitations_invitee', 'user_invitations', type_='unique')

    # 删除索引
    op.drop_index('ix_user_invitations_inviter_invitee', table_name='user_invitations')
    op.drop_index('ix_user_invitations_invitee_id', table_name='user_invitations')
    op.drop_index('ix_user_invitations_inviter_id', table_name='user_invitations')

    # 删除表
    op.drop_table('user_invitations')

    # 删除users表字段
    op.drop_index('ix_users_invited_by', table_name='users')
    op.drop_column('users', 'invited_by')
    op.drop_index('ix_users_invite_code', table_name='users')
    op.drop_column('users', 'invite_code')
