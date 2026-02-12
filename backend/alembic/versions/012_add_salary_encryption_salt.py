"""add encryption_salt column to salary_records

Revision ID: 012
Revises: 011
Create Date: 2025-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str]], None] = None


def upgrade() -> None:
    # 添加 encryption_salt 列到 salary_records 表
    op.add_column(
        "salary_records",
        sa.Column("encryption_salt", sa.String(44), nullable=False, comment="加密使用的盐值 (base64编码)")
    )

    # 为现有记录生成默认 salt（向后兼容）
    # 注意：这些旧记录需要重新加密才能获得唯一 salt 的安全性提升
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE salary_records SET encryption_salt = :default_salt WHERE encryption_salt IS NULL"
        ),
        {"default_salt": "LEGACY_SALT_REPLACE_BEFORE_USE"}  # 标记为需要迁移的记录
    )


def downgrade() -> None:
    op.drop_column("salary_records", "encryption_salt")
