"""Boot the real FastAPI app for browser (Playwright) verification.

Uses the same fakes as the pytest suite (deterministic embeddings + scripted LLM) because
the sandbox cannot reach Hugging Face or Gemini.  Everything else - PostgreSQL, Alembic,
ChromaDB, BM25, the ingestion queue, auth - is the production code path.

    python -m tests.e2e_server            # http://127.0.0.1:8000
"""

import os

from tests import conftest  # noqa: F401  (sets env vars and installs the fakes on import)
from alembic import command
from alembic.config import Config
from sqlalchemy import text

import uvicorn

from app.database.session import engine


def main() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(conftest.BACKEND_DIR / "alembic.ini")), "head")
    uvicorn.run(conftest.app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), log_level="warning")


if __name__ == "__main__":
    main()
