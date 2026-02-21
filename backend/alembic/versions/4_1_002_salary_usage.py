"""salary usage records table

Revision ID: 4_1_002
Revises: 4_1_001
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4_1_002'
down_revision = '4_1_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'salary_usage_records',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('salary_record_id', sa.String(36), nullable=False, comment='薪资记录ID'),
        sa.Column('usage_type', sa.String(50), nullable=False, comment='使用类型: housing/food/transport/shopping/entertainment/medical/education/other'),
        sa.Column('amount', sa.String(100), nullable=False, comment='使用金额（加密）'),
        sa.Column('usage_date', sa.DateTime(), nullable=False, comment='使用日期'),
        sa.Column('description', sa.Text(), nullable=True, comment='备注说明'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['salary_record_id'], ['salary_records.id'], ondelete='CASCADE'),
        # Indexes
        sa.Index('idx_salary_usage_records_id', 'id'),
        sa.Index('idx_salary_usage_records_user_id', 'user_id'),
        sa.Index('idx_salary_usage_records_salary_record_id', 'salary_record_id'),
        sa.Index('idx_salary_usage_records_usage_type', 'usage_type'),
        sa.Index('idx_salary_usage_records_usage_date', 'usage_date'),
        comment='薪资使用记录表'
    )


def downgrade():
    op.drop_table('salary_usage_records')
