"""add visibility column to posts table

Revision ID: 87bf6d84d693
Revises: 5f7a896fdd53
Create Date: 2026-02-19 22:41:08.889045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87bf6d84d693'
down_revision: Union[str, None] = '5f7a896fdd53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add visibility column to posts table
    # SQLite doesn't support ALTER TABLE with ENUM directly, so use VARCHAR
    op.add_column('posts', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public', comment='公开范围: public=公开, followers=关注者可见, private=仅自己可见'))


def downgrade() -> None:
    op.drop_column('posts', 'visibility')
