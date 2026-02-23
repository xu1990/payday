"""qrcode_mapping_table

Revision ID: 374f1dc72d5a
Revises: 4_6_002
Create Date: 2026-02-23 10:50:06.810267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '374f1dc72d5a'
down_revision: Union[str, None] = '4_6_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建二维码参数映射表
    op.create_table(
        'qrcode_mappings',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('short_code', sa.String(16), unique=True, nullable=False, comment='唯一短码（6-8位）'),
        sa.Column('page', sa.String(200), nullable=False, comment='小程序页面路径'),
        sa.Column('params', sa.JSON(), nullable=False, comment='自定义参数（JSON格式）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间（可选）'),
        sa.Column('scan_count', sa.Integer(), server_default='0', nullable=False, comment='扫描次数'),
        comment='二维码参数映射表'
    )

    # 创建索引
    op.create_index('idx_qrcodemapping_short_code', 'qrcode_mappings', ['short_code'])
    op.create_index('idx_qrcodemapping_expires_at', 'qrcode_mappings', ['expires_at'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_qrcodemapping_expires_at', table_name='qrcode_mappings')
    op.drop_index('idx_qrcodemapping_short_code', table_name='qrcode_mappings')

    # 删除表
    op.drop_table('qrcode_mappings')
