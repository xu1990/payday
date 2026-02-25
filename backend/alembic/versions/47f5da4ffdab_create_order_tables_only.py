"""create order tables only

Revision ID: 47f5da4ffdab
Revises: a86ed29cae9c
Create Date: 2026-02-24 09:55:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '47f5da4ffdab'
down_revision: Union[str, None] = 'a86ed29cae9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create orders table (if not exists)
    # Using batch operations for SQLite compatibility
    try:
        op.create_table('orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('order_number', sa.String(length=32), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Total amount in fen/cents'),
        sa.Column('points_used', sa.Integer(), nullable=False, server_default='0', comment='Points used'),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00', comment='Discount amount in fen/cents'),
        sa.Column('shipping_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00', comment='Shipping cost in fen/cents'),
        sa.Column('final_amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Final amount in fen/cents'),
        sa.Column('payment_method', sa.Enum('wechat', 'alipay', 'points', 'hybrid', name='order_payment_method'), nullable=False),
        sa.Column('payment_status', sa.Enum('pending', 'paid', 'failed', 'refunded', name='order_payment_status'), nullable=False, server_default='pending'),
        sa.Column('transaction_id', sa.String(length=100), nullable=True, comment='Payment transaction ID'),
        sa.Column('paid_at', sa.DateTime(), nullable=True, comment='Payment timestamp'),
        sa.Column('status', sa.Enum('pending', 'paid', 'processing', 'shipped', 'delivered', 'completed', 'cancelled', 'refunding', 'refunded', name='order_status'), nullable=False, server_default='pending'),
        sa.Column('shipping_address_id', sa.String(length=36), nullable=True),
        sa.Column('shipping_template_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shipping_address_id'], ['user_addresses.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_orders_order_number', 'orders', ['order_number'], unique=True)
        op.create_index('ix_orders_payment_status', 'orders', ['payment_status'], unique=False)
        op.create_index('ix_orders_status', 'orders', ['status'], unique=False)
        op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)
        op.create_index('ix_orders_shipping_address_id', 'orders', ['shipping_address_id'], unique=False)
    except Exception as e:
        # Table might already exist in production
        if 'already exists' not in str(e):
            raise

    # Create order_items table (if not exists)
    try:
        op.create_table('order_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('sku_id', sa.String(length=36), nullable=True),
        sa.Column('product_name', sa.String(length=100), nullable=False, comment='Product name snapshot'),
        sa.Column('sku_name', sa.String(length=100), nullable=True, comment='SKU name snapshot'),
        sa.Column('product_image', sa.String(length=500), nullable=True, comment='Product image URL'),
        sa.Column('attributes', sa.JSON(), nullable=True, comment='SKU attributes snapshot'),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False, comment='Unit price in fen/cents'),
        sa.Column('quantity', sa.Integer(), nullable=False, comment='Quantity'),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False, comment='Subtotal in fen/cents'),
        sa.Column('bundle_components', sa.JSON(), nullable=True, comment='Bundle components snapshot'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)
        op.create_index('ix_order_items_product_id', 'order_items', ['product_id'], unique=False)
    except Exception as e:
        # Table might already exist in production
        if 'already exists' not in str(e):
            raise


def downgrade() -> None:
    op.drop_index('ix_order_items_product_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')
    op.drop_index('ix_orders_shipping_address_id', table_name='orders')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_payment_status', table_name='orders')
    op.drop_index('ix_orders_order_number', table_name='orders')
    op.drop_table('orders')
