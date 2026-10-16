"""create doctors and patients tables"""

from alembic import op
import sqlalchemy as sa

revision = "0001_doctors_patients"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("specialty", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=False, unique=True),
        sa.Column("phone", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("room", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False, server_default="UNDISCLOSED"),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_patients_full_name", "patients", ["full_name"])


def downgrade():
    op.drop_index("ix_patients_full_name", table_name="patients")
    op.drop_table("patients")
    op.drop_table("doctors")
