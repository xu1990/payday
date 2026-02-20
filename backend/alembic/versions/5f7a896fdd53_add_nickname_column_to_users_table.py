"""add nickname column to users table

Revision ID: 5f7a896fdd53
Revises: c6747998338b
Create Date: 2026-02-19 22:38:45.446785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f7a896fdd53'
down_revision: Union[str, None] = 'c6747998338b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nickname column to users table
    op.add_column('users', sa.Column('nickname', sa.String(length=50), nullable=True, comment='显示昵称'))


def downgrade() -> None:
    op.drop_column('users', 'nickname')
