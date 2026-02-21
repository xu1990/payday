"""phone login support

Revision ID: 4_1_001
Revises: ed629cd327d5
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4_1_001'
down_revision = 'ed629cd327d5'
branch_labels = None
depends_on = None


def upgrade():
    # Add phone number fields
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True, comment='手机号（加密存储）'))
    op.add_column('users', sa.Column('phone_verified', sa.Integer, server_default='0', comment='手机号是否验证（0=未验证，1=已验证）'))

    # Create index for phone lookups
    op.create_index('idx_users_phone', 'users', ['phone_number'])


def downgrade():
    # Remove index first
    op.drop_index('idx_users_phone', table_name='users')

    # Remove columns
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone_number')
