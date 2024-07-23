"""Add temperature column to role table

Revision ID: add_temperature_to_role
Revises: 
Create Date: 2024-07-23 12:44:02.750000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'add_temperature_to_role'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if the column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('role')
    if 'temperature' not in [col['name'] for col in columns]:
        # Add the column with a default value
        op.add_column('role', sa.Column('temperature', sa.Float(), server_default='0.7', nullable=False))
        print("Added 'temperature' column to 'role' table.")
    else:
        print("'temperature' column already exists in 'role' table.")

    # Ensure all existing rows have the default value
    op.execute(text("UPDATE role SET temperature = 0.7 WHERE temperature IS NULL"))


def downgrade():
    op.drop_column('role', 'temperature')