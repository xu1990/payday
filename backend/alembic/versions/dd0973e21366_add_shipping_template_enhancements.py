"""add_shipping_template_enhancements

Revision ID: dd0973e21366
Revises: 21a3020333e4
Create Date: 2026-02-26 10:17:13.028270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd0973e21366'
down_revision: Union[str, None] = '21a3020333e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ShippingTemplate new fields
    op.add_column('shipping_templates',
        sa.Column('free_shipping_type', sa.String(20), nullable=False, server_default='none',
                  comment='包邮类型: none/amount/quantity/seller'))
    op.add_column('shipping_templates',
        sa.Column('free_quantity', sa.Integer(), nullable=True,
                  comment='满件数包邮阈值'))
    op.add_column('shipping_templates',
        sa.Column('excluded_regions', sa.JSON(), nullable=True,
                  comment='不配送区域JSON'))
    op.add_column('shipping_templates',
        sa.Column('volume_unit', sa.Integer(), nullable=True,
                  comment='体积单位(cm³)'))

    # ShippingTemplateRegion new fields
    op.add_column('shipping_template_regions',
        sa.Column('free_quantity', sa.Integer(), nullable=True,
                  comment='区域满件数包邮阈值'))
    op.add_column('shipping_template_regions',
        sa.Column('is_excluded', sa.Boolean(), nullable=False, server_default='0',
                  comment='是否不配送区域'))


def downgrade() -> None:
    op.drop_column('shipping_template_regions', 'is_excluded')
    op.drop_column('shipping_template_regions', 'free_quantity')
    op.drop_column('shipping_templates', 'volume_unit')
    op.drop_column('shipping_templates', 'excluded_regions')
    op.drop_column('shipping_templates', 'free_quantity')
    op.drop_column('shipping_templates', 'free_shipping_type')
