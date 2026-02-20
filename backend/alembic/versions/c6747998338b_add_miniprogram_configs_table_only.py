"""add miniprogram_configs table only

Revision ID: c6747998338b
Revises: 013
Create Date: 2026-02-19 22:29:26.353203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6747998338b'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create miniprogram_configs table
    op.create_table('miniprogram_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False, comment='配置键'),
        sa.Column('value', sa.Text(), nullable=True, comment='配置值（JSON或文本）'),
        sa.Column('description', sa.String(length=200), nullable=True, comment='配置说明'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否启用', server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序', server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )


def downgrade() -> None:
    op.drop_table('miniprogram_configs')
