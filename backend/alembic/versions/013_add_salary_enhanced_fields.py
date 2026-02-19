"""add salary enhanced fields

Revision ID: 013
Revises: 012
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str]] = None


def upgrade() -> None:
    # 添加 salary_records 表的增强字段（Sprint 3.3）
    op.add_column(
        'salary_records',
        sa.Column('pre_tax_amount', sa.Numeric(precision=10, scale=2), nullable=True, comment='税前金额（分）')
    )
    op.add_column(
        'salary_records',
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=True, comment='扣税金额（分）')
    )
    op.add_column(
        'salary_records',
        sa.Column('source', sa.String(length=50), nullable=True, comment='来源：公司/工厂/其他')
    )
    op.add_column(
        'salary_records',
        sa.Column('delayed_days', sa.Integer(), nullable=True, comment='延迟天数')
    )


def downgrade() -> None:
    op.drop_column('salary_records', 'delayed_days')
    op.drop_column('salary_records', 'source')
    op.drop_column('salary_records', 'tax_amount')
    op.drop_column('salary_records', 'pre_tax_amount')
