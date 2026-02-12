"""create users payday_configs salary_records

Revision ID: 001
Revises:
Create Date: 2025-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("openid", sa.String(64), nullable=False),
        sa.Column("unionid", sa.String(64), nullable=True),
        sa.Column("anonymous_name", sa.String(50), nullable=False),
        sa.Column("avatar", sa.String(255), nullable=True),
        sa.Column("bio", sa.String(200), nullable=True),
        sa.Column("follower_count", sa.Integer(), default=0),
        sa.Column("following_count", sa.Integer(), default=0),
        sa.Column("post_count", sa.Integer(), default=0),
        sa.Column("allow_follow", sa.Integer(), default=1),
        sa.Column("allow_comment", sa.Integer(), default=1),
        sa.Column("status", sa.Enum("normal", "disabled", name="user_status"), nullable=False, server_default="normal"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_openid", "users", ["openid"], unique=True)

    op.create_table(
        "payday_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_name", sa.String(50), nullable=False),
        sa.Column("payday", sa.Integer(), nullable=False),
        sa.Column("calendar_type", sa.Enum("solar", "lunar", name="calendar_type_enum"), nullable=False, server_default="solar"),
        sa.Column("estimated_salary", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payday_configs_user_id", "payday_configs", ["user_id"])

    op.create_table(
        "salary_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("config_id", sa.String(36), sa.ForeignKey("payday_configs.id"), nullable=False),
        sa.Column("amount_encrypted", sa.Text(), nullable=False),
        sa.Column("payday_date", sa.Date(), nullable=False),
        sa.Column("salary_type", sa.Enum("normal", "bonus", "allowance", "other", name="salary_type_enum"), nullable=False, server_default="normal"),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("mood", sa.Enum("happy", "relief", "sad", "angry", "expect", name="mood_enum"), nullable=False),
        sa.Column("risk_status", sa.Enum("pending", "approved", "rejected", name="risk_status_enum"), nullable=False, server_default="pending"),
        sa.Column("risk_check_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_salary_records_user_id", "salary_records", ["user_id"])
    op.create_index("ix_salary_records_config_id", "salary_records", ["config_id"])
    op.create_index("ix_salary_records_payday_date", "salary_records", ["payday_date"])


def downgrade() -> None:
    op.drop_table("salary_records")
    op.drop_table("payday_configs")
    op.drop_table("users")
