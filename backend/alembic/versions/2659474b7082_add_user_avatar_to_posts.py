"""add user_avatar to posts

Revision ID: 2659474b7082
Revises: a19f4f22cb92
Create Date: 2026-02-23 21:21:25.403934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '2659474b7082'
down_revision: Union[str, None] = 'a19f4f22cb92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_avatar column to posts table
    op.add_column('posts', sa.Column('user_avatar', sa.String(255), nullable=True, comment='发帖时用户头像URL冗余'))

    # Backfill existing posts with user avatar from users table
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE posts p
        LEFT JOIN users u ON p.user_id = u.id
        SET p.user_avatar = u.avatar
        WHERE p.user_avatar IS NULL
    """))


def downgrade() -> None:
    op.drop_column('posts', 'user_avatar')
