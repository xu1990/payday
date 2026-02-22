"""add first salary usage table

Revision ID: 4_1_004
Revises: 4_1_003
Create Date: 2026-02-22 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4_1_004'
down_revision: Union[str, None] = '4_1_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create first_salary_usage_records table
    op.create_table(
        'first_salary_usage_records',
        sa.Column('id', sa.String(length=36), nullable=False, comment='主键ID'),
        sa.Column('user_id', sa.String(length=36), nullable=False, comment='用户ID'),
        sa.Column('salary_record_id', sa.String(length=36), nullable=False, comment='工资记录ID'),
        sa.Column('usage_category', sa.String(length=50), nullable=False, comment='用途分类'),
        sa.Column('usage_subcategory', sa.String(length=50), nullable=True, comment='子分类'),
        sa.Column('amount', sa.String(length=100), nullable=False, comment='用途金额（加密）'),
        sa.Column('note', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['salary_record_id'], ['salary_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_first_salary_usage_records_salary_record_id', 'first_salary_usage_records', ['salary_record_id'], unique=False)
    op.create_index('ix_first_salary_usage_records_user_id', 'first_salary_usage_records', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_first_salary_usage_records_salary_record_id', table_name='first_salary_usage_records')
    op.drop_index('ix_first_salary_usage_records_user_id', table_name='first_salary_usage_records')
    op.drop_table('first_salary_usage_records')
