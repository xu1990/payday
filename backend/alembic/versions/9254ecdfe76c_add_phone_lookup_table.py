"""add phone lookup table

Revision ID: 4_1_003
Revises: 4_1_002
Create Date: 2025-02-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4_1_003'
down_revision = '4_1_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 phone_lookup 表（兼容SQLite和MySQL）
    op.create_table(
        'phone_lookup',
        sa.Column('id', sa.String(36), primary_key=True, comment='主键ID'),
        sa.Column('phone_hash', sa.String(64), nullable=False, comment='手机号SHA-256哈希'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),

        # 外键约束（SQLite和MySQL都支持CASCADE）
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_phone_lookup_user', ondelete='CASCADE'),

        # 唯一约束和索引
        sa.UniqueConstraint('phone_hash', name='uq_phone_lookup_hash'),
        comment='手机号查找表 - 用于快速根据手机号查找用户'
    )

    # 创建索引
    op.create_index('idx_phone_lookup_hash', 'phone_lookup', ['phone_hash'])
    op.create_index('idx_phone_lookup_user_id', 'phone_lookup', ['user_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_phone_lookup_user_id', table_name='phone_lookup')
    op.drop_index('idx_phone_lookup_hash', table_name='phone_lookup')

    # 删除表
    op.drop_table('phone_lookup')
