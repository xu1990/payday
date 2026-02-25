"""add_created_at_updated_at_to_order_shipments

Revision ID: d5d122463a8e
Revises: f553d41dcbe7
Create Date: 2026-02-24 22:56:20.817261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5d122463a8e'
down_revision: Union[str, None] = 'f553d41dcbe7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_at and updated_at columns to order_shipments
    op.add_column('order_shipments', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'))
    op.add_column('order_shipments', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'))

    # For existing rows, set created_at and updated_at to shipped_at if it exists
    op.execute("""
        UPDATE order_shipments
        SET created_at = shipped_at,
            updated_at = shipped_at
        WHERE created_at IS NULL OR updated_at IS NULL
    """)


def downgrade() -> None:
    op.drop_column('order_shipments', 'updated_at')
    op.drop_column('order_shipments', 'created_at')
