"""add_locked_points_field

Revision ID: 76794333b897
Revises: 4_7_005
Create Date: 2026-02-28 19:50:15.308239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76794333b897'
down_revision: Union[str, None] = '4_7_005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 locked_points 字段到 ability_points 表
    op.add_column(
        'ability_points',
        sa.Column('locked_points', sa.Integer(), nullable=False, server_default='0',
                 comment='锁定积分（支付中）')
    )


def downgrade() -> None:
    op.drop_column('ability_points', 'locked_points')
