"""first_salary_usage_records table

Revision ID: 4_1_004
Revises: 4_1_001
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '4_1_004'
down_revision = '4_1_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'first_salary_usage_records',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('salary_record_id', sa.String(36), nullable=False, comment='工资记录ID'),
        sa.Column('usage_category', sa.String(50), nullable=False, comment='用途分类'),
        sa.Column('usage_subcategory', sa.String(50), nullable=True, comment='子分类'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='用途金额'),
        sa.Column('note', sa.Text, nullable=True, comment='备注'),
        sa.Column('is_first_salary', sa.Integer, nullable=False, default=1, comment='是否为第一笔工资'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fsur_user_fk'),
        sa.ForeignKeyConstraint(['salary_record_id'], ['salary_records.id'], ondelete='CASCADE', name='fsur_salary_fk'),

        comment='第一笔工资用途记录表'
    )

    # 创建索引
    op.create_index('idx_fsur_user_id', 'first_salary_usage_records', ['user_id'])
    op.create_index('idx_fsur_salary_record_id', 'first_salary_usage_records', ['salary_record_id'])
    op.create_index('idx_fsur_is_first_salary', 'first_salary_usage_records', ['is_first_salary'])


def downgrade():
    # 删除索引
    op.drop_index('idx_fsur_is_first_salary', table_name='first_salary_usage_records')
    op.drop_index('idx_fsur_salary_record_id', table_name='first_salary_usage_records')
    op.drop_index('idx_fsur_user_id', table_name='first_salary_usage_records')

    # 删除表
    op.drop_table('first_salary_usage_records')
