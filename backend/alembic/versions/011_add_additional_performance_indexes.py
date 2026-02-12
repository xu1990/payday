"""add additional performance indexes

Revision ID: 011
Revises: 010_add_membership_and_checkin_tables
Create Date: 2026-02-12

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # users表额外索引
    op.create_index('ix_users_status_created', 'users', ['status', 'created_at'])

    # posts表新增复合索引
    op.create_index('ix_posts_status_risk_created', 'posts',
                  ['status', 'risk_status', 'created_at'])
    op.create_index('ix_posts_user_created', 'posts',
                  ['user_id', 'created_at'])
    op.create_index('ix_posts_like_count', 'posts', ['like_count'])

    # comments表新增索引
    op.create_index('ix_comments_post_created', 'comments',
                  ['post_id', 'created_at'])

    # likes表唯一索引（防止重复点赞）
    op.create_index('ix_likes_unique', 'likes',
                  ['user_id', 'target_type', 'target_id'], unique=True)

    # membership_orders表索引
    op.create_index('ix_orders_user_status', 'membership_orders',
                  ['user_id', 'status'])
    op.create_index('ix_orders_transaction', 'membership_orders',
                  ['transaction_id'])


def downgrade():
    op.drop_index('ix_orders_transaction')
    op.drop_index('ix_orders_user_status')
    op.drop_index('ix_likes_unique')
    op.drop_index('ix_comments_post_created')
    op.drop_index('ix_posts_like_count')
    op.drop_index('ix_posts_user_created')
    op.drop_index('ix_posts_status_risk_created')
    op.drop_index('ix_users_status_created')
