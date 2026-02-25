"""checkin_enhancement - Sprint 4.5 Enhanced Check-in Features

Revision ID: 4_5_001
Revises: 4_4_001
Create Date: 2026-02-22

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_5_001'
down_revision = '4_4_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to check_ins table
    op.add_column('check_ins', sa.Column('checkin_type', sa.String(50), nullable=True, server_default='daily',
                                          comment='打卡类型: daily/weekly/milestone/special'))
    op.add_column('check_ins', sa.Column('reward_points', sa.Integer(), nullable=True, server_default='0',
                                          comment='奖励积分'))
    op.add_column('check_ins', sa.Column('streak_days', sa.Integer(), nullable=True, server_default='0',
                                          comment='连续打卡天数'))
    op.add_column('check_ins', sa.Column('mood', sa.String(50), nullable=True,
                                          comment='打卡时的心情'))
    op.add_column('check_ins', sa.Column('tags', sa.JSON(), nullable=True,
                                          comment='打卡标签 JSON'))

    # Create index for checkin_type
    op.create_index('idx_checkin_type', 'check_ins', ['checkin_type'])


def downgrade():
    # Drop index
    op.drop_index('idx_checkin_type', table_name='check_ins')

    # Drop columns
    op.drop_column('check_ins', 'tags')
    op.drop_column('check_ins', 'mood')
    op.drop_column('check_ins', 'streak_days')
    op.drop_column('check_ins', 'reward_points')
    op.drop_column('check_ins', 'checkin_type')
