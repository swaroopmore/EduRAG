"""create study plans table

Revision ID: 01b77c1791b2
Revises: f0a3ae4f69f8
Create Date: 2026-07-12 14:25:53.561519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01b77c1791b2'
down_revision: Union[str, Sequence[str], None] = 'f0a3ae4f69f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(

        "study_plans",

        sa.Column(
            "day",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "time",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "duration",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "subject_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(

            ["user_id"],

            ["users.id"],

            ondelete="CASCADE",

        ),

        sa.ForeignKeyConstraint(

            ["subject_id"],

            ["subjects.id"],

            ondelete="CASCADE",

        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

    )


def downgrade() -> None:

    op.drop_table(
        "study_plans"
    )
