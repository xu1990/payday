"""salary_mood_and_arrears_enhancement

Revision ID: 4_3_001
Revises: 4_2_001
Create Date: 2026-02-22

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_3_001'
down_revision = '4_2_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to salary_records for Sprint 4.3
    op.add_column('salary_records', sa.Column('is_arrears', sa.Integer(), nullable=True, server_default='0', comment='是否拖欠'))
    op.add_column('salary_records', sa.Column('arrears_amount', sa.Numeric(10, 2), nullable=True, comment='拖欠金额'))
    op.add_column('salary_records', sa.Column('mood_note', sa.Text(), nullable=True, comment='心情备注'))
    op.add_column('salary_records', sa.Column('mood_tags', sa.JSON(), nullable=True, comment='心情标签 JSON'))

    # Create index for arrears queries
    op.create_index('idx_salary_is_arrears', 'salary_records', ['is_arrears'])


def downgrade():
    # Drop index
    op.drop_index('idx_salary_is_arrears', table_name='salary_records')

    # Drop columns
    op.drop_column('salary_records', 'mood_tags')
    op.drop_column('salary_records', 'mood_note')
    op.drop_column('salary_records', 'arrears_amount')
    op.drop_column('salary_records', 'is_arrears')
