from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.config import settings
from app.database.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/")
def root():
    return {"message": "Welcome to EduRAG API", "status": "running"}


@router.get("/health")
def health():
    """Cheap liveness probe (use this for Railway's health check)."""
    return {"status": "healthy"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: database + vector store reachable. Exposes no secrets."""
    db.execute(text("SELECT 1"))
    vectors = get_vectorstore().count()
    return {
        "status": "ready" if vectors >= 0 else "degraded",
        "database": "ok",
        "vector_store": "ok" if vectors >= 0 else "unavailable",
        "vectors": vectors,
        "environment": settings.ENVIRONMENT,
    }
