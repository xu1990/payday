"""add deactivated_at to users table

Revision ID: 090c6cd520b3
Revises: 87bf6d84d693
Create Date: 2026-02-19 23:28:33.236927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '090c6cd520b3'
down_revision: Union[str, None] = '87bf6d84d693'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deactivated_at column for soft delete functionality
    op.add_column('users', sa.Column('deactivated_at', sa.DateTime(), nullable=True, comment='注销时间（软删除）'))
    # Create index on deactivated_at for efficient queries
    op.create_index('idx_users_deactivated_at', 'users', ['deactivated_at'])


def downgrade() -> None:
    # Drop index first
    op.drop_index('idx_users_deactivated_at', table_name='users')
    # Remove deactivated_at column
    op.drop_column('users', 'deactivated_at')
