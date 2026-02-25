"""add point shop system - Sprint 4.7

Revision ID: 4_7_002
Revises: 4_7_001
Create Date: 2026-02-23

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_7_002'
down_revision = '4_7_001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建point_products表
    op.create_table(
        'point_products',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='商品名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='商品描述'),
        sa.Column('image_url', sa.String(500), nullable=True, comment='商品图片URL'),
        sa.Column('points_cost', sa.Integer(), nullable=False, comment='积分价格'),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0', comment='库存数量'),
        sa.Column('stock_unlimited', sa.Boolean(), nullable=False, server_default='false', comment='库存无限'),
        sa.Column('category', sa.String(50), nullable=True, comment='商品分类'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否上架'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        comment='积分商品表'
    )

    # 创建商品表索引
    op.create_index('ix_point_products_is_active', 'point_products', ['is_active'])
    op.create_index('ix_point_products_category', 'point_products', ['category'])
    op.create_index('ix_point_products_sort_order', 'point_products', ['sort_order'])

    # 2. 创建point_orders表
    op.create_table(
        'point_orders',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('product_id', sa.String(36), nullable=False, comment='商品ID'),
        sa.Column('order_number', sa.String(32), nullable=False, unique=True, comment='订单号'),
        sa.Column('product_name', sa.String(100), nullable=False, comment='商品名称快照'),
        sa.Column('product_image', sa.String(500), nullable=True, comment='商品图片快照'),
        sa.Column('points_cost', sa.Integer(), nullable=False, comment='消耗积分快照'),
        sa.Column('delivery_info', sa.Text(), nullable=True, comment='收货信息JSON'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('status', sa.Enum('pending', 'completed', 'cancelled', 'refunded', name='point_order_status'), nullable=False, server_default='pending', comment='订单状态'),
        sa.Column('admin_id', sa.String(36), nullable=True, comment='处理管理员ID'),
        sa.Column('processed_at', sa.TIMESTAMP(), nullable=True, comment='处理时间'),
        sa.Column('notes_admin', sa.Text(), nullable=True, comment='管理员备注'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='po_user_fk'),
        sa.ForeignKeyConstraint(['product_id'], ['point_products.id'], ondelete='RESTRICT', name='po_product_fk'),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], ondelete='SET NULL', name='po_admin_fk'),

        comment='积分订单表'
    )

    # 创建订单表索引
    op.create_index('ix_point_orders_user_id', 'point_orders', ['user_id'])
    op.create_index('ix_point_orders_order_number', 'point_orders', ['order_number'])
    op.create_index('ix_point_orders_status', 'point_orders', ['status'])
    op.create_index('ix_point_orders_product_id', 'point_orders', ['product_id'])
    op.create_index('ix_point_orders_created_at', 'point_orders', ['created_at'])


def downgrade():
    # 删除索引
    op.drop_index('ix_point_orders_created_at', table_name='point_orders')
    op.drop_index('ix_point_orders_product_id', table_name='point_orders')
    op.drop_index('ix_point_orders_status', table_name='point_orders')
    op.drop_index('ix_point_orders_order_number', table_name='point_orders')
    op.drop_index('ix_point_orders_user_id', table_name='point_orders')

    # 删除订单表
    op.drop_table('point_orders')

    # 删除索引
    op.drop_index('ix_point_products_sort_order', table_name='point_products')
    op.drop_index('ix_point_products_category', table_name='point_products')
    op.drop_index('ix_point_products_is_active', table_name='point_products')

    # 删除商品表
    op.drop_table('point_products')
