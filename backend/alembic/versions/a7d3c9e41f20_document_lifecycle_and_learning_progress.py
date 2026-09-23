"""document lifecycle, learning progress, indexes and cascades

Revision ID: a7d3c9e41f20
Revises: 01b77c1791b2
Create Date: 2026-09-23 10:00:00.000000

* documents: processing status/stage/error, page + chunk counts, owner column
  (backfilled from subjects) - existing documents are marked READY because they
  were indexed synchronously by the previous pipeline.
* notes.keywords, flashcards.mastered, study_plans.quote/completed
* quiz_attempts table (server-graded quiz submissions)
* chat_history foreign keys now cascade so subjects/users can be deleted
* indexes on the columns every query filters by
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7d3c9e41f20"
down_revision: Union[str, Sequence[str], None] = "01b77c1791b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------ documents
    op.add_column(
        "documents",
        sa.Column("status", sa.String(20), nullable=False, server_default="ready"),
    )
    op.alter_column("documents", "status", server_default=None)
    op.add_column("documents", sa.Column("stage", sa.String(30), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("chunk_count", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("documents", sa.Column("user_id", sa.UUID(), nullable=True))
    op.execute(
        """
        UPDATE documents
        SET user_id = subjects.user_id
        FROM subjects
        WHERE documents.subject_id = subjects.id
        """
    )
    op.execute("UPDATE documents SET processed_at = created_at WHERE processed_at IS NULL")
    op.alter_column("documents", "user_id", nullable=False)
    op.create_foreign_key(
        "documents_user_id_fkey", "documents", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_index("ix_documents_subject_id", "documents", ["subject_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # ------------------------------------------------------------- subjects
    op.create_index("ix_subjects_user_id", "subjects", ["user_id"])

    # --------------------------------------------------------- chat_history
    # The migration that recreated this table forgot the timestamp defaults the
    # ORM relies on (server_default=now()); without them inserts fail.
    op.execute("ALTER TABLE chat_history ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE chat_history ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE chat_history DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey")
    op.execute("ALTER TABLE chat_history DROP CONSTRAINT IF EXISTS chat_history_subject_id_fkey")
    op.create_foreign_key(
        "chat_history_user_id_fkey", "chat_history", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "chat_history_subject_id_fkey",
        "chat_history",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_chat_history_user_subject_created",
        "chat_history",
        ["user_id", "subject_id", "created_at"],
    )

    # ---------------------------------------------------------------- notes
    op.add_column("notes", sa.Column("keywords", postgresql.JSONB(), nullable=True))
    op.create_index("ix_notes_user_id", "notes", ["user_id"])
    op.create_index("ix_notes_subject_id", "notes", ["subject_id"])

    # ----------------------------------------------------------- flashcards
    op.add_column(
        "flashcards",
        sa.Column("mastered", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_flashcards_user_id", "flashcards", ["user_id"])
    op.create_index("ix_flashcards_subject_id", "flashcards", ["subject_id"])

    # -------------------------------------------------------------- quizzes
    op.create_index("ix_quizzes_user_id", "quizzes", ["user_id"])
    op.create_index("ix_quizzes_subject_id", "quizzes", ["subject_id"])

    # ---------------------------------------------------------- study_plans
    op.add_column("study_plans", sa.Column("quote", sa.String(), nullable=True))
    op.add_column(
        "study_plans",
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_study_plans_user_id", "study_plans", ["user_id"])
    op.create_index("ix_study_plans_subject_id", "study_plans", ["subject_id"])

    # ------------------------------------------------------- quiz_attempts
    op.create_table(
        "quiz_attempts",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_subject_id", "quiz_attempts", ["subject_id"])


def downgrade() -> None:
    op.drop_table("quiz_attempts")

    op.drop_index("ix_study_plans_subject_id", table_name="study_plans")
    op.drop_index("ix_study_plans_user_id", table_name="study_plans")
    op.drop_column("study_plans", "completed")
    op.drop_column("study_plans", "quote")

    op.drop_index("ix_quizzes_subject_id", table_name="quizzes")
    op.drop_index("ix_quizzes_user_id", table_name="quizzes")

    op.drop_index("ix_flashcards_subject_id", table_name="flashcards")
    op.drop_index("ix_flashcards_user_id", table_name="flashcards")
    op.drop_column("flashcards", "mastered")

    op.drop_index("ix_notes_subject_id", table_name="notes")
    op.drop_index("ix_notes_user_id", table_name="notes")
    op.drop_column("notes", "keywords")

    op.drop_index("ix_chat_history_user_subject_created", table_name="chat_history")
    op.execute("ALTER TABLE chat_history DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey")
    op.execute("ALTER TABLE chat_history DROP CONSTRAINT IF EXISTS chat_history_subject_id_fkey")
    op.create_foreign_key(
        "chat_history_user_id_fkey", "chat_history", "users", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "chat_history_subject_id_fkey", "chat_history", "subjects", ["subject_id"], ["id"]
    )

    op.drop_index("ix_subjects_user_id", table_name="subjects")

    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_subject_id", table_name="documents")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_constraint("documents_user_id_fkey", "documents", type_="foreignkey")
    for column in (
        "user_id",
        "processed_at",
        "chunk_count",
        "page_count",
        "error_message",
        "stage",
        "status",
    ):
        op.drop_column("documents", column)
