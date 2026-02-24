"""create work_records table

Revision ID: 54ab08875266
Revises: 2659474b7082
Create Date: 2026-02-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54ab08875266'
down_revision = '2659474b7082'
branch_labels = None
depends_on = None


def upgrade():
    # Create work_records table
    op.create_table(
        'work_records',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('post_id', sa.String(36), nullable=False),
        sa.Column('clock_in_time', sa.DateTime(), nullable=False, comment='打卡开始时间'),
        sa.Column('clock_out_time', sa.DateTime(), nullable=True, comment='打卡结束时间'),
        sa.Column('work_duration_minutes', sa.Integer(), nullable=True, comment='工作时长（分钟）'),
        sa.Column('work_type', sa.Enum('regular', 'overtime', 'weekend', 'holiday', name='work_type_enum'), nullable=False, comment='工作类型'),
        sa.Column('overtime_hours', sa.Numeric(precision=4, scale=2), nullable=False, comment='加班时长'),
        sa.Column('location', sa.String(200), nullable=True, comment='工作地点'),
        sa.Column('company_name', sa.String(100), nullable=True, comment='公司名称'),
        sa.Column('mood', sa.String(20), nullable=True, comment='心情'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签'),
        sa.Column('content', sa.String(2000), nullable=False, comment='工作内容'),
        sa.Column('images', sa.JSON(), nullable=True, comment='图片列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', name='uq_work_records_post_id')
    )
    op.create_index(op.f('ix_work_records_user_id'), 'work_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_work_records_clock_in_time'), 'work_records', ['clock_in_time'], unique=False)
    op.create_index(op.f('ix_work_records_work_type'), 'work_records', ['work_type'], unique=False)
    op.create_index(op.f('ix_work_records_overtime_hours'), 'work_records', ['overtime_hours'], unique=False)


def downgrade():
    op.drop_constraint('uq_work_records_post_id', 'work_records', type_='unique')
    op.drop_index(op.f('ix_work_records_overtime_hours'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_work_type'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_clock_in_time'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_user_id'), table_name='work_records')
    op.drop_table('work_records')
