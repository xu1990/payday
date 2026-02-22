"""savings_goals table

Revision ID: 4_4_001
Revises: 4_3_001
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4_4_001'
down_revision = '4_3_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'savings_goals',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('title', sa.String(100), nullable=False, comment='目标标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='目标描述'),
        sa.Column('target_amount', sa.Numeric(10, 2), nullable=False, comment='目标金额'),
        sa.Column('current_amount', sa.Numeric(10, 2), nullable=False, server_default='0', comment='当前已存金额'),
        sa.Column('deadline', sa.Date(), nullable=True, comment='目标截止日期'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='目标开始日期'),
        sa.Column('status', sa.Enum('active', 'completed', 'cancelled', 'paused', name='savings_goal_status'),
                  nullable=False, server_default='active', comment='目标状态'),
        sa.Column('category', sa.String(50), nullable=True, comment='目标分类'),
        sa.Column('icon', sa.String(50), nullable=True, comment='图标'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True, comment='完成时间'),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='sg_user_fk'),

        comment='存款目标表'
    )

    # 创建索引
    op.create_index('idx_sg_user_id', 'savings_goals', ['user_id'])
    op.create_index('idx_sg_status', 'savings_goals', ['status'])
    op.create_index('idx_sg_category', 'savings_goals', ['category'])


def downgrade():
    # 删除索引
    op.drop_index('idx_sg_category', table_name='savings_goals')
    op.drop_index('idx_sg_status', table_name='savings_goals')
    op.drop_index('idx_sg_user_id', table_name='savings_goals')

    # 删除表
    op.drop_table('savings_goals')
