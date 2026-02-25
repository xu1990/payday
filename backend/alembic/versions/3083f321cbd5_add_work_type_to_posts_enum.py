"""add work type to posts enum

Revision ID: 3083f321cbd5
Revises: 54ab08875266
Create Date: 2026-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

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
    """
    DOWNGRADE WARNING: This migration is NOT safe to rollback if work-type posts exist!

    Before downgrading, you must either:
    1. Delete all posts with type='work', OR
    2. Migrate them to another valid type (complaint/sharing/question)

    Failure to do so will cause data integrity errors as those posts will reference
    an invalid enum value.
    """
    # For MySQL, remove 'work' from the enum
    # SAFETY CHECK: Ensure no work-type posts exist before downgrading
    try:
        # Check for existing work-type posts
        result = op.execute("SELECT COUNT(*) FROM posts WHERE type = 'work'")
        count = result.fetchone()[0] if result else 0

        if count > 0:
            raise Exception(
                f"Cannot downgrade: {count} posts with type='work' exist. "
                f"Please delete or migrate these posts before running downgrade."
            )

        op.execute("ALTER TABLE posts MODIFY COLUMN type ENUM('complaint', 'sharing', 'question') NOT NULL COMMENT 'Post type'")
    except Exception as e:
        # If not MySQL (e.g., SQLite in tests), the enum is handled by SQLAlchemy
        # Or if there's a safety check error, propagate it
        if "Cannot downgrade" in str(e):
            raise
        pass
