"""add point shop admin tables

Revision ID: d313b8b1a806
Revises: 7923ea874537
Create Date: 2026-02-24 21:03:13.128809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd313b8b1a806'
down_revision: Union[str, None] = '7923ea874537'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables exist before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create point_categories table
    if 'point_categories' not in existing_tables:
        op.create_table(
            'point_categories',
            sa.Column('id', sa.String(length=36), nullable=False, comment='分类ID'),
            sa.Column('name', sa.String(length=50), nullable=False, comment='分类名称'),
            sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
            sa.Column('parent_id', sa.String(length=36), nullable=True, comment='父分类ID'),
            sa.Column('icon_url', sa.String(length=500), nullable=True, comment='分类图标URL'),
            sa.Column('banner_url', sa.String(length=500), nullable=True, comment='分类横幅URL'),
            sa.Column('level', sa.Integer(), nullable=False, server_default='1', comment='层级(1/2/3)'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.ForeignKeyConstraint(['parent_id'], ['point_categories.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            comment='积分商城商品分类表'
        )
        op.create_index(op.f('ix_point_categories_parent_id'), 'point_categories', ['parent_id'], unique=False)

    # Create point_specifications table
    if 'point_specifications' not in existing_tables:
        op.create_table(
            'point_specifications',
            sa.Column('id', sa.String(length=36), nullable=False, comment='规格ID'),
            sa.Column('product_id', sa.String(length=36), nullable=False, comment='商品ID'),
            sa.Column('name', sa.String(length=50), nullable=False, comment='规格名称'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.ForeignKeyConstraint(['product_id'], ['point_products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            comment='积分商品规格表（如：颜色、尺寸）'
        )
        op.create_index(op.f('ix_point_specifications_product_id'), 'point_specifications', ['product_id'], unique=False)

    # Create point_specification_values table
    if 'point_specification_values' not in existing_tables:
        op.create_table(
            'point_specification_values',
            sa.Column('id', sa.String(length=36), nullable=False, comment='规格值ID'),
            sa.Column('specification_id', sa.String(length=36), nullable=False, comment='规格ID'),
            sa.Column('value', sa.String(length=50), nullable=False, comment='规格值'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.ForeignKeyConstraint(['specification_id'], ['point_specifications.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            comment='积分商品规格值表（如：红色、蓝色）'
        )
        op.create_index(op.f('ix_point_specification_values_specification_id'), 'point_specification_values', ['specification_id'], unique=False)

    # Create point_product_skus table
    if 'point_product_skus' not in existing_tables:
        op.create_table(
            'point_product_skus',
            sa.Column('id', sa.String(length=36), nullable=False, comment='SKU ID'),
            sa.Column('product_id', sa.String(length=36), nullable=False, comment='商品ID'),
            sa.Column('sku_code', sa.String(length=50), nullable=False, comment='SKU编码'),
            sa.Column('specs', sa.Text(), nullable=False, comment='规格组合JSON'),
            sa.Column('stock', sa.Integer(), nullable=False, server_default='0', comment='库存数量'),
            sa.Column('stock_unlimited', sa.Boolean(), nullable=False, server_default='0', comment='库存无限'),
            sa.Column('points_cost', sa.Integer(), nullable=False, server_default='0', comment='积分价格'),
            sa.Column('image_url', sa.String(length=500), nullable=True, comment='SKU专属图片'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.ForeignKeyConstraint(['product_id'], ['point_products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sku_code', name='uq_point_product_skus_code'),
            comment='积分商品SKU表'
        )
        op.create_index(op.f('ix_point_product_skus_product_id'), 'point_product_skus', ['product_id'], unique=False)
        op.create_index(op.f('ix_point_product_skus_sku_code'), 'point_product_skus', ['sku_code'], unique=True)

    # Create point_returns table
    if 'point_returns' not in existing_tables:
        op.create_table(
            'point_returns',
            sa.Column('id', sa.String(length=36), nullable=False, comment='退货ID'),
            sa.Column('order_id', sa.String(length=36), nullable=False, comment='订单ID'),
            sa.Column('reason', sa.Text(), nullable=False, comment='退货原因'),
            sa.Column('status', sa.Enum('requested', 'approved', 'rejected', name='point_return_status'), nullable=False, server_default='requested', comment='退货状态'),
            sa.Column('admin_notes', sa.Text(), nullable=True, comment='管理员备注'),
            sa.Column('admin_id', sa.String(length=36), nullable=True, comment='处理管理员ID'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='申请时间'),
            sa.Column('processed_at', sa.DateTime(), nullable=True, comment='处理时间'),
            sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['order_id'], ['point_orders.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            comment='积分订单退货表'
        )
        op.create_index(op.f('ix_point_returns_order_id'), 'point_returns', ['order_id'], unique=False)

    # Add columns to point_products table
    columns = [col['name'] for col in inspector.get_columns('point_products')]

    if 'category_id' not in columns:
        op.add_column('point_products', sa.Column('category_id', sa.String(length=36), nullable=True, comment='分类ID'))
        op.create_index(op.f('ix_point_products_category_id'), 'point_products', ['category_id'], unique=False)
        # Note: Foreign key constraints are not added for SQLite compatibility
        # The application layer will enforce referential integrity

    if 'has_sku' not in columns:
        op.add_column('point_products', sa.Column('has_sku', sa.Boolean(), nullable=False, server_default='0', comment='是否启用SKU管理'))

    # Add columns to point_orders table
    order_columns = [col['name'] for col in inspector.get_columns('point_orders')]

    if 'sku_id' not in order_columns:
        op.add_column('point_orders', sa.Column('sku_id', sa.String(length=36), nullable=True, comment='SKU ID'))
        # Note: Foreign key not added for SQLite compatibility

    if 'address_id' not in order_columns:
        op.add_column('point_orders', sa.Column('address_id', sa.String(length=36), nullable=True, comment='收货地址ID'))
        # Note: Foreign key not added for SQLite compatibility

    if 'shipment_id' not in order_columns:
        op.add_column('point_orders', sa.Column('shipment_id', sa.String(length=36), nullable=True, comment='发货ID'))
        # Note: Foreign key not added for SQLite compatibility


def downgrade() -> None:
    # Remove columns from point_orders
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    order_columns = [col['name'] for col in inspector.get_columns('point_orders')]

    if 'shipment_id' in order_columns:
        op.drop_column('point_orders', 'shipment_id')

    if 'address_id' in order_columns:
        op.drop_column('point_orders', 'address_id')

    if 'sku_id' in order_columns:
        op.drop_column('point_orders', 'sku_id')

    # Remove columns from point_products
    product_columns = [col['name'] for col in inspector.get_columns('point_products')]

    if 'has_sku' in product_columns:
        op.drop_column('point_products', 'has_sku')

    if 'category_id' in product_columns:
        op.drop_index(op.f('ix_point_products_category_id'), table_name='point_products')
        op.drop_column('point_products', 'category_id')

    # Drop tables
    existing_tables = inspector.get_table_names()

    if 'point_returns' in existing_tables:
        op.drop_index(op.f('ix_point_returns_order_id'), table_name='point_returns')
        op.drop_table('point_returns')

    if 'point_product_skus' in existing_tables:
        op.drop_index(op.f('ix_point_product_skus_sku_code'), table_name='point_product_skus')
        op.drop_index(op.f('ix_point_product_skus_product_id'), table_name='point_product_skus')
        op.drop_table('point_product_skus')

    if 'point_specification_values' in existing_tables:
        op.drop_index(op.f('ix_point_specification_values_specification_id'), table_name='point_specification_values')
        op.drop_table('point_specification_values')

    if 'point_specifications' in existing_tables:
        op.drop_index(op.f('ix_point_specifications_product_id'), table_name='point_specifications')
        op.drop_table('point_specifications')

    if 'point_categories' in existing_tables:
        op.drop_index(op.f('ix_point_categories_parent_id'), table_name='point_categories')
        op.drop_table('point_categories')
