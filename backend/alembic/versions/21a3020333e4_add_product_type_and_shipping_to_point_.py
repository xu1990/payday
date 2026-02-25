"""add_product_type_and_shipping_to_point_products

Revision ID: 21a3020333e4
Revises: d5d122463a8e
Create Date: 2026-02-24 23:00:04.776402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21a3020333e4'
down_revision: Union[str, None] = 'd5d122463a8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加商品类型、物流方式和运费模板字段
    op.add_column('point_products',
        sa.Column('product_type', sa.String(20), nullable=False, server_default='physical', comment='商品类型')
    )
    op.add_column('point_products',
        sa.Column('shipping_method', sa.String(20), nullable=False, server_default='express', comment='物流方式')
    )
    op.add_column('point_products',
        sa.Column('shipping_template_id', sa.String(36), nullable=True, comment='运费模板ID')
    )

    # 创建索引
    op.create_index('ix_point_products_shipping_template_id', 'point_products', ['shipping_template_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_point_products_shipping_template_id', table_name='point_products')

    # 删除列
    op.drop_column('point_products', 'shipping_template_id')
    op.drop_column('point_products', 'shipping_method')
    op.drop_column('point_products', 'product_type')
