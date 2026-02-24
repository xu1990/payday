"""add work type to posts enum

Revision ID: 3083f321cbd5
Revises: 54ab08875266
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3083f321cbd5'
down_revision: Union[str, None] = '54ab08875266'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For MySQL, modify the enum to include 'work' type
    # Note: SQLite doesn't support ALTER COLUMN for enum, but the model change works for tests
    try:
        op.execute("ALTER TABLE posts MODIFY COLUMN type ENUM('complaint', 'sharing', 'question', 'work') NOT NULL COMMENT 'Post type'")
    except Exception:
        # If not MySQL (e.g., SQLite in tests), the enum is handled by SQLAlchemy
        pass


def downgrade() -> None:
    # For MySQL, remove 'work' from the enum
    try:
        op.execute("ALTER TABLE posts MODIFY COLUMN type ENUM('complaint', 'sharing', 'question') NOT NULL COMMENT 'Post type'")
    except Exception:
        # If not MySQL (e.g., SQLite in tests), the enum is handled by SQLAlchemy
        pass
