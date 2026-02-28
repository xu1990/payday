"""add sold fields to products and skus

Revision ID: 4_7_004
Revises: 8e4733b8a83b
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_7_004'
down_revision = '8e4733b8a83b'
branch_labels = None
depends_on = None


def upgrade():
    # Add sold field to point_products table
    op.add_column('point_products',
                  sa.Column('sold', sa.Integer(), nullable=False, server_default='0', comment='已售数量'))

    # Add sold field to point_product_skus table
    op.add_column('point_product_skus',
                  sa.Column('sold', sa.Integer(), nullable=False, server_default='0', comment='已售数量'))


def downgrade():
    # Remove sold field from point_product_skus table
    op.drop_column('point_product_skus', 'sold')

    # Remove sold field from point_products table
    op.drop_column('point_products', 'sold')
