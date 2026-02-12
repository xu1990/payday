"""add performance indexes

Revision ID: 20250212_add_indexes
Revises:
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250212_add_indexes'
down_revision = None  # Set to the latest migration if needed
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加性能优化索引"""

    # Post 表索引
    # risk_status 索引 - 用于风控审核查询
    op.create_index(
        'ix_post_risk_status',
        'post',
        ['risk_status'],
        postgresql_where=sa.text("risk_status IS NOT NULL")
    )

    # status + created_at 复合索引 - 用于查询正常状态的帖子
    op.create_index(
        'ix_post_status_created_at',
        'post',
        ['status', sa.text('created_at DESC')]
    )

    # user_id + created_at 复合索引 - 用于用户帖子列表
    op.create_index(
        'ix_post_user_id_created_at',
        'post',
        ['user_id', sa.text('created_at DESC')]
    )

    # Comment 表索引
    # parent_id 索引 - 用于回复查询
    op.create_index(
        'ix_comment_parent_id',
        'comment',
        ['parent_id'],
        postgresql_where=sa.text("parent_id IS NOT NULL")
    )

    # post_id + created_at 复合索引 - 用于帖子评论列表
    op.create_index(
        'ix_comment_post_id_created_at',
        'comment',
        ['post_id', sa.text('created_at DESC')]
    )

    # Like 表索引
    # user_id + target_type 复合索引 - 用于用户点赞记录查询
    op.create_index(
        'ix_like_user_id_target_type',
        'like',
        ['user_id', 'target_type']
    )

    # Follow 表索引
    # follower_id + created_at 复合索引 - 用于关注列表查询
    op.create_index(
        'ix_follow_follower_id_created_at',
        'follow',
        ['follower_id', sa.text('created_at DESC')]
    )

    # following_id + created_at 复合索引 - 用于粉丝列表查询
    op.create_index(
        'ix_follow_following_id_created_at',
        'follow',
        ['following_id', sa.text('created_at DESC')]
    )

    # MembershipOrder 表索引
    # user_id + created_at 复合索引 - 用于用户订单查询
    op.create_index(
        'ix_membership_order_user_id_created_at',
        'membership_order',
        ['user_id', sa.text('created_at DESC')]
    )

    # status + created_at 复合索引 - 用于订单状态查询
    op.create_index(
        'ix_membership_order_status_created_at',
        'membership_order',
        ['status', sa.text('created_at DESC')]
    )

    # Share 表索引
    # user_id + created_at 复合索引 - 用于用户分享记录查询
    op.create_index(
        'ix_share_user_id_created_at',
        'share',
        ['user_id', sa.text('created_at DESC')]
    )


def downgrade() -> None:
    """移除添加的索引"""

    # Post 表
    op.drop_index('ix_post_risk_status', table_name='post')
    op.drop_index('ix_post_status_created_at', table_name='post')
    op.drop_index('ix_post_user_id_created_at', table_name='post')

    # Comment 表
    op.drop_index('ix_comment_parent_id', table_name='comment')
    op.drop_index('ix_comment_post_id_created_at', table_name='comment')

    # Like 表
    op.drop_index('ix_like_user_id_target_type', table_name='like')

    # Follow 表
    op.drop_index('ix_follow_follower_id_created_at', table_name='follow')
    op.drop_index('ix_follow_following_id_created_at', table_name='follow')

    # MembershipOrder 表
    op.drop_index('ix_membership_order_user_id_created_at', table_name='membership_order')
    op.drop_index('ix_membership_order_status_created_at', table_name='membership_order')

    # Share 表
    op.drop_index('ix_share_user_id_created_at', table_name='share')
