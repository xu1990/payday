"""phone login support

Revision ID: 4_1_001
Revises: ed629cd327d5
Create Date: 2026-02-21

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4_1_001'
down_revision = 'ed629cd327d5'
branch_labels = None
depends_on = None


def upgrade():
    # Add phone number fields - check if they exist first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'phone_number' not in columns:
        op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True, comment='手机号（加密存储）'))

    if 'phone_verified' not in columns:
        op.add_column('users', sa.Column('phone_verified', sa.Integer, server_default='0', comment='手机号是否验证（0=未验证，1=已验证）'))

    # Create index for phone lookups if it doesn't exist
    indexes = inspector.get_indexes('users')
    index_names = [idx['name'] for idx in indexes]
    if 'idx_users_phone' not in index_names:
        op.create_index('idx_users_phone', 'users', ['phone_number'])


def downgrade():
    # Remove index first (if exists)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Try to drop index if it exists
    try:
        indexes = inspector.get_indexes('users')
        index_names = [idx['name'] for idx in indexes]
        if 'idx_users_phone' in index_names:
            op.drop_index('idx_users_phone', table_name='users')
    except Exception:
        pass

    # Remove columns (if exist)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'phone_verified' in columns:
        op.drop_column('users', 'phone_verified')

    if 'phone_number' in columns:
        op.drop_column('users', 'phone_number')
