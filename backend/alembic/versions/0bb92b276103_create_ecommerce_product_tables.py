"""create ecommerce product tables

Revision ID: 0bb92b276103
Revises: 3083f321cbd5
Create Date: 2026-02-24 09:34:39.512526

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0bb92b276103'
down_revision: Union[str, None] = '3083f321cbd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create product tables ###
    op.create_table('product_categories',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False, comment='分类名称'),
    sa.Column('code', sa.String(length=50), nullable=False, comment='分类代码'),
    sa.Column('parent_id', sa.String(length=36), nullable=True),
    sa.Column('icon', sa.String(length=200), nullable=True, comment='图标URL'),
    sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序'),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否启用'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['product_categories.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_product_categories_parent_id'), 'product_categories', ['parent_id'], unique=False)

    op.create_table('products',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False, comment='商品名称'),
    sa.Column('description', sa.String(length=2000), nullable=True, comment='商品描述'),
    sa.Column('images', sa.JSON(), nullable=True, comment='商品图片URLs'),
    sa.Column('category_id', sa.String(length=36), nullable=True),
    sa.Column('product_type', sa.Enum('point', 'cash', 'hybrid', name='product_type_enum'), nullable=False),
    sa.Column('item_type', sa.Enum('physical', 'virtual', 'bundle', name='item_type_enum'), nullable=False),
    sa.Column('bundle_type', sa.Enum('pre_configured', 'custom_builder', name='bundle_type_enum'), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_virtual', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('seo_keywords', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    op.create_table('product_skus',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('product_id', sa.String(length=36), nullable=False),
    sa.Column('sku_code', sa.String(length=50), nullable=False, comment='SKU代码'),
    sa.Column('name', sa.String(length=100), nullable=False, comment='SKU名称'),
    sa.Column('attributes', sa.JSON(), nullable=False, comment='规格属性'),
    sa.Column('stock', sa.Integer(), nullable=False, comment='库存'),
    sa.Column('stock_unlimited', sa.Boolean(), nullable=False, comment='库存无限'),
    sa.Column('images', sa.JSON(), nullable=True, comment='SKU图片'),
    sa.Column('weight_grams', sa.Integer(), nullable=True, comment='重量(克)'),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sku_code')
    )
    op.create_index(op.f('ix_product_skus_product_id'), 'product_skus', ['product_id'], unique=False)

    op.create_table('product_bundles',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('bundle_product_id', sa.String(length=36), nullable=False),
    sa.Column('component_product_id', sa.String(length=36), nullable=False),
    sa.Column('component_sku_id', sa.String(length=36), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False, comment='数量'),
    sa.Column('is_required', sa.Boolean(), nullable=False, comment='是否必选'),
    sa.ForeignKeyConstraint(['bundle_product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['component_product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['component_sku_id'], ['product_skus.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_bundles_bundle_product_id'), 'product_bundles', ['bundle_product_id'], unique=False)
    op.create_index(op.f('ix_product_bundles_component_product_id'), 'product_bundles', ['component_product_id'], unique=False)

    op.create_table('product_prices',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('sku_id', sa.String(length=36), nullable=False),
    sa.Column('price_type', sa.Enum('base', 'member', 'bulk', 'promotion', name='price_type_enum'), nullable=False),
    sa.Column('price_amount', sa.Integer(), nullable=False, comment='价格(分或积分)'),
    sa.Column('currency', sa.Enum('CNY', 'POINTS', name='price_currency_enum'), nullable=False),
    sa.Column('min_quantity', sa.Integer(), nullable=False, comment='最小数量'),
    sa.Column('membership_level', sa.Integer(), nullable=True, comment='会员等级'),
    sa.Column('valid_from', sa.DateTime(), nullable=True),
    sa.Column('valid_until', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['sku_id'], ['product_skus.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_prices_sku_id'), 'product_prices', ['sku_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Drop product tables ###
    op.drop_index(op.f('ix_product_prices_sku_id'), table_name='product_prices')
    op.drop_table('product_prices')

    op.drop_index(op.f('ix_product_bundles_component_product_id'), table_name='product_bundles')
    op.drop_index(op.f('ix_product_bundles_bundle_product_id'), table_name='product_bundles')
    op.drop_table('product_bundles')

    op.drop_index(op.f('ix_product_skus_product_id'), table_name='product_skus')
    op.drop_table('product_skus')

    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_table('products')

    op.drop_index(op.f('ix_product_categories_parent_id'), table_name='product_categories')
    op.drop_table('product_categories')
    # ### end Alembic commands ###
