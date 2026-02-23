"""update post timestamps to not null

Revision ID: update_post_timestamps
Revises: add_topic_ids
Create Date: 2026-02-23 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'update_post_timestamps'
down_revision: Union[str, None] = 'add_topic_ids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 不支持直接 ALTER COLUMN 设置 NOT NULL
    # 需要重建表
    op.execute("""
        CREATE TABLE posts_new (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            anonymous_name VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            images JSON,
            tags JSON,
            type VARCHAR(20) NOT NULL DEFAULT 'complaint',
            salary_range VARCHAR(20),
            industry VARCHAR(50),
            city VARCHAR(50),
            topic_id VARCHAR(36),
            topic_ids JSON,
            visibility VARCHAR(20) NOT NULL DEFAULT 'public',
            view_count INTEGER NOT NULL DEFAULT 0,
            like_count INTEGER NOT NULL DEFAULT 0,
            comment_count INTEGER NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'normal',
            risk_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            risk_score INTEGER,
            risk_reason VARCHAR(255),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        );
    """)

    op.execute("""
        INSERT INTO posts_new
        SELECT * FROM posts;
    """)

    op.execute("""
        DROP TABLE posts;
    """)

    op.execute("""
        ALTER TABLE posts_new RENAME TO posts;
    """)

    # 重建索引
    op.execute("""
        CREATE INDEX ix_posts_user_id ON posts(user_id);
        CREATE INDEX ix_posts_topic_id ON posts(topic_id);
    """)


def downgrade() -> None:
    # 回滚：允许 NULL
    pass
