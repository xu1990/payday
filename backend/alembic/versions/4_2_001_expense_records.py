"""expense_records table

Revision ID: 4_2_001
Revises: 4_1_004
Create Date: 2026-02-22

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4_2_001'
down_revision = '4_1_004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'expense_records',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('salary_record_id', sa.String(36), nullable=False, comment='工资记录ID'),
        sa.Column('expense_date', sa.Date(), nullable=False, comment='支出日期'),
        sa.Column('category', sa.String(50), nullable=False, comment='支出分类'),
        sa.Column('subcategory', sa.String(50), nullable=True, comment='子分类'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='支出金额（加密）'),
        sa.Column('note', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='exp_user_fk'),
        sa.ForeignKeyConstraint(['salary_record_id'], ['salary_records.id'], ondelete='CASCADE', name='exp_salary_fk'),
        
        comment='支出记录表'
    )
    
    # 创建索引
    op.create_index('idx_exp_user_id', 'expense_records', ['user_id'])
    op.create_index('idx_exp_salary_record_id', 'expense_records', ['salary_record_id'])
    op.create_index('idx_exp_expense_date', 'expense_records', ['expense_date'])
    op.create_index('idx_exp_category', 'expense_records', ['category'])


def downgrade():
    # 删除索引
    op.drop_index('idx_exp_category', table_name='expense_records')
    op.drop_index('idx_exp_expense_date', table_name='expense_records')
    op.drop_index('idx_exp_salary_record_id', table_name='expense_records')
    op.drop_index('idx_exp_user_id', table_name='expense_records')
    
    # 删除表
    op.drop_table('expense_records')
