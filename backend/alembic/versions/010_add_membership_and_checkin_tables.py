"""add membership tables

Revision ID: 010_add_membership_and_checkin_tables
Revises: 009
Create Date: 2025-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "010_add_membership_and_checkin_tables"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 会员套餐表
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, comment="套餐名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="权益说明"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, comment="月费（分）"),
        sa.Column("duration_days", sa.Integer(), nullable=False, comment="有效期（天数）"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1", comment="是否启用"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="排序"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 会员订单表
    op.create_table(
        "membership_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("membership_id", sa.String(36), sa.ForeignKey("memberships.id"), nullable=False, comment="套餐ID"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False, comment="实付金额（分）"),
        sa.Column("status", sa.Enum("pending", "paid", "cancelled", "refunded", name="order_status_enum"), nullable=False, server_default="pending"),
        sa.Column("payment_method", sa.String(20), nullable=True, comment="支付方式：wechat/alipay"),
        sa.Column("transaction_id", sa.String(100), nullable=True, comment="第三方交易ID"),
        sa.Column("start_date", sa.DateTime(), nullable=False, comment="会员开始日期"),
        sa.Column("end_date", sa.DateTime(), nullable=True, comment="会员到期日期"),
        sa.Column("auto_renew", sa.Integer(), nullable=False, server_default="0", comment="是否自动续费"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_membership_orders_user_id", "membership_orders", ["user_id"])


def downgrade() -> None:
    op.drop_table("membership_orders")
    op.drop_table("memberships")
