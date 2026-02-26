"""add_specification_template_table

Revision ID: 8e4733b8a83b
Revises: dd0973e21366
Create Date: 2026-02-26 15:53:48.250288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e4733b8a83b'
down_revision: Union[str, None] = 'dd0973e21366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only create specification_templates table
    op.create_table('specification_templates',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False, comment='规格名称'),
    sa.Column('description', sa.String(length=200), nullable=True, comment='规格描述'),
    sa.Column('values_json', sa.Text(), nullable=False, comment='规格值列表JSON'),
    sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序权重'),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否启用'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('specification_templates')
