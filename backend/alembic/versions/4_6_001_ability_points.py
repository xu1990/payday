"""ability_points_system - Sprint 4.6 Ability Points System

Revision ID: 4_6_001
Revises: 4_5_001
Create Date: 2026-02-22

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_6_001'
down_revision = '4_5_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create ability_points table
    op.create_table(
        'ability_points',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True, comment='用户ID'),
        sa.Column('total_points', sa.Integer(), nullable=False, server_default='0', comment='总积分'),
        sa.Column('available_points', sa.Integer(), nullable=False, server_default='0', comment='可用积分'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1', comment='等级'),
        sa.Column('total_earned', sa.Integer(), nullable=False, server_default='0', comment='累计获得积分'),
        sa.Column('total_spent', sa.Integer(), nullable=False, server_default='0', comment='累计消费积分'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='ap_user_fk'),

        comment='用户能力值积分表'
    )

    # Create ability_point_transactions table
    op.create_table(
        'ability_point_transactions',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('amount', sa.Integer(), nullable=False, comment='积分变动'),
        sa.Column('balance_after', sa.Integer(), nullable=False, comment='变动后余额'),
        sa.Column('transaction_type', sa.String(50), nullable=False, comment='交易类型'),
        sa.Column('event_type', sa.String(50), nullable=True, comment='事件类型'),
        sa.Column('reference_id', sa.String(36), nullable=True, comment='关联记录ID'),
        sa.Column('reference_type', sa.String(50), nullable=True, comment='关联记录类型'),
        sa.Column('description', sa.String(200), nullable=True, comment='交易描述'),
        sa.Column('metadata', sa.Text(), nullable=True, comment='额外信息 JSON'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='apt_user_fk'),

        comment='积分流水记录'
    )

    # Create point_redemptions table
    op.create_table(
        'point_redemptions',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('reward_name', sa.String(100), nullable=False, comment='奖励名称'),
        sa.Column('reward_type', sa.String(50), nullable=False, comment='奖励类型'),
        sa.Column('points_cost', sa.Integer(), nullable=False, comment='消耗积分'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', comment='状态'),
        sa.Column('delivery_info', sa.Text(), nullable=True, comment='配送信息 JSON'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('admin_id', sa.String(36), nullable=True, comment='审核管理员ID'),
        sa.Column('processed_at', sa.TIMESTAMP(), nullable=True, comment='处理时间'),
        sa.Column('rejection_reason', sa.String(200), nullable=True, comment='拒绝原因'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='pr_user_fk'),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], name='pr_admin_fk'),

        comment='积分兑换记录'
    )

    # Create indexes
    op.create_index('idx_ap_user_id', 'ability_points', ['user_id'])
    op.create_index('idx_ap_level', 'ability_points', ['level'])

    op.create_index('idx_apt_user_id', 'ability_point_transactions', ['user_id'])
    op.create_index('idx_apt_transaction_type', 'ability_point_transactions', ['transaction_type'])
    op.create_index('idx_apt_created_at', 'ability_point_transactions', ['created_at'])

    op.create_index('idx_pr_user_id', 'point_redemptions', ['user_id'])
    op.create_index('idx_pr_status', 'point_redemptions', ['status'])
    op.create_index('idx_pr_reward_type', 'point_redemptions', ['reward_type'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_pr_reward_type', table_name='point_redemptions')
    op.drop_index('idx_pr_status', table_name='point_redemptions')
    op.drop_index('idx_pr_user_id', table_name='point_redemptions')

    op.drop_index('idx_apt_created_at', table_name='ability_point_transactions')
    op.drop_index('idx_apt_transaction_type', table_name='ability_point_transactions')
    op.drop_index('idx_apt_user_id', table_name='ability_point_transactions')

    op.drop_index('idx_ap_level', table_name='ability_points')
    op.drop_index('idx_ap_user_id', table_name='ability_points')

    # Drop tables
    op.drop_table('point_redemptions')
    op.drop_table('ability_point_transactions')
    op.drop_table('ability_points')
