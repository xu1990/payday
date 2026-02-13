"""create check_ins table

Revision ID: 006
Revises: 005
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'check_ins',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('check_date', sa.Date(), nullable=False, comment='打卡日期', index=True),
        sa.Column('note', sa.String(500), nullable=True, comment='打卡备注'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade():
    op.drop_table('check_ins')
