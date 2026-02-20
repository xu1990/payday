"""add_follow_type_to_notifications_enum

Revision ID: ed629cd327d5
Revises: af1fc110a7d4
Create Date: 2026-02-20 20:58:38.732302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed629cd327d5'
down_revision: Union[str, None] = 'af1fc110a7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'follow' to the notification_type_enum
    # In MySQL, we need to modify the ENUM definition
    op.execute("""
        ALTER TABLE notifications
        MODIFY COLUMN type ENUM('comment', 'reply', 'like', 'system', 'follow')
        NOT NULL
    """)


def downgrade() -> None:
    # Remove 'follow' from the notification_type_enum
    # First, delete any follow notifications to avoid constraint violations
    op.execute("DELETE FROM notifications WHERE type = 'follow'")
    # Then modify the ENUM back to original values
    op.execute("""
        ALTER TABLE notifications
        MODIFY COLUMN type ENUM('comment', 'reply', 'like', 'system')
        NOT NULL
    """)
