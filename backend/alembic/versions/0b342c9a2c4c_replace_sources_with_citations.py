"""replace sources with citations

Revision ID: 0b342c9a2c4c
Revises: 79d24614bc4e
Create Date: 2026-07-06 23:43:17.755741
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "0b342c9a2c4c"
down_revision: Union[str, Sequence[str], None] = "79d24614bc4e"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # Delete old table
    op.drop_table("chat_history")

    # Recreate with new schema
    op.create_table(
        "chat_history",

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),

        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id"),
            nullable=False,
        ),

        sa.Column(
            "question",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "normalized_question",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "answer",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "citations",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_chat_history_user_id",
        "chat_history",
        ["user_id"],
    )

    op.create_index(
        "ix_chat_history_subject_id",
        "chat_history",
        ["subject_id"],
    )

    op.create_index(
        "ix_chat_history_normalized_question",
        "chat_history",
        ["normalized_question"],
    )


def downgrade() -> None:
    pass