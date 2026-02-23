"""add topic_ids field to posts

Revision ID: add_topic_ids
Revises: 4_7_002
Create Date: 2026-02-23 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_topic_ids'
down_revision: Union[str, None] = '4_7_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 使用 JSON 类型需要 TEXT 存储
    with op.batch_alter_table('posts') as batch_op:
        batch_op.add_column(sa.Column('topic_ids', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('posts') as batch_op:
        batch_op.drop_column('topic_ids')
