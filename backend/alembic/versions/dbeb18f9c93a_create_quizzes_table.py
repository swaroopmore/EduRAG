"""create quizzes table

Revision ID: dbeb18f9c93a
Revises: dcb474dbb5cf
Create Date: 2026-07-12 10:39:13.981605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbeb18f9c93a'
down_revision: Union[str, Sequence[str], None] = 'dcb474dbb5cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "quizzes",

        sa.Column(
            "question",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "option_a",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "option_b",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "option_c",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "option_d",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "correct_answer",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "explanation",
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

        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:

    op.drop_table("quizzes")
