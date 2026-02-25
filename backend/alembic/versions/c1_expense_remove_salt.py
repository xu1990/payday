"""remove amount_salt from expense_records

Revision ID: c1_expense_remove_salt
Revises: 374f1dc72d5a
Create Date: 2026-02-23 13:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c1_expense_remove_salt'
down_revision = '374f1dc72d5a'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support DROP COLUMN directly, need to recreate table
    op.execute("""
        CREATE TABLE expense_records_new (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            salary_record_id VARCHAR(36) NOT NULL,
            expense_date DATE NOT NULL,
            category VARCHAR(50) NOT NULL,
            subcategory VARCHAR(50),
            amount NUMERIC(10, 2) NOT NULL,
            note TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(salary_record_id) REFERENCES salary_records (id)
        )
    """)

    op.execute("""
        INSERT INTO expense_records_new (id, user_id, salary_record_id, expense_date, category, subcategory, amount, note, created_at, updated_at)
        SELECT id, user_id, salary_record_id, expense_date, category, subcategory, amount, note, created_at, updated_at
        FROM expense_records
    """)

    op.execute("DROP TABLE expense_records")
    op.execute("ALTER TABLE expense_records_new RENAME TO expense_records")

    op.execute("CREATE INDEX ix_expense_records_category ON expense_records(category)")
    op.execute("CREATE INDEX ix_expense_records_expense_date ON expense_records(expense_date)")
    op.execute("CREATE INDEX ix_expense_records_salary_record_id ON expense_records(salary_record_id)")
    op.execute("CREATE INDEX ix_expense_records_user_id ON expense_records(user_id)")


def downgrade():
    # For rollback, recreate with amount_salt column
    op.execute("""
        CREATE TABLE expense_records_new (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            salary_record_id VARCHAR(36) NOT NULL,
            expense_date DATE NOT NULL,
            category VARCHAR(50) NOT NULL,
            subcategory VARCHAR(50),
            amount NUMERIC(10, 2) NOT NULL,
            amount_salt VARCHAR(88) NOT NULL DEFAULT '',
            note TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(salary_record_id) REFERENCES salary_records (id)
        )
    """)

    op.execute("""
        INSERT INTO expense_records_new (id, user_id, salary_record_id, expense_date, category, subcategory, amount, amount_salt, note, created_at, updated_at)
        SELECT id, user_id, salary_record_id, expense_date, category, subcategory, amount, '' as amount_salt, note, created_at, updated_at
        FROM expense_records
    """)

    op.execute("DROP TABLE expense_records")
    op.execute("ALTER TABLE expense_records_new RENAME TO expense_records")

    op.execute("CREATE INDEX ix_expense_records_category ON expense_records(category)")
    op.execute("CREATE INDEX ix_expense_records_expense_date ON expense_records(expense_date)")
    op.execute("CREATE INDEX ix_expense_records_salary_record_id ON expense_records(salary_record_id)")
    op.execute("CREATE INDEX ix_expense_records_user_id ON expense_records(user_id)")
