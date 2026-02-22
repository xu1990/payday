"""add_amount_salt_to_expense_records - Sprint 4.6 Expense Amount Encryption

Revision ID: 4_6_002
Revises: 4_6_001
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4_6_002'
down_revision = '4_6_001'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 amount_salt 列到 expense_records 表
    op.add_column(
        'expense_records',
        sa.Column('amount_salt', sa.String(88), nullable=False, server_default='', comment='金额加密盐值')
    )

    # 为现有记录生成默认 salt（向后兼容）
    # 注意：这些旧记录需要重新加密才能获得唯一 salt 的安全性提升
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE expense_records SET amount_salt = :default_salt WHERE amount_salt = ''"
        ),
        {"default_salt": "LEGACY_SALT_REPLACE_BEFORE_USE"}  # 标记为需要迁移的记录
    )

    # 添加复合索引以提高查询性能
    op.create_index(
        'idx_expense_user_date',
        'expense_records',
        ['user_id', 'expense_date']
    )


def downgrade():
    op.drop_index('idx_expense_user_date', 'expense_records')
    op.drop_column('expense_records', 'amount_salt')
