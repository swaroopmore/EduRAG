from fastapi import APIRouter

from app.api.routes import (
    auth,
    chat,
    dashboard,
    database,
    documents,
    flashcards,
    health,
    subject,
    test_ai,
    test_retriever,quiz,
)

api_router = APIRouter()

# Health
api_router.include_router(
    health.router,
    tags=["Health"],
)

# Database
api_router.include_router(
    database.router,
    tags=["Database"],
)

# Authentication
api_router.include_router(
    auth.router,
)

# Dashboard
api_router.include_router(
    dashboard.router,
)

# Subjects
api_router.include_router(
    subject.router,
)

# Documents
api_router.include_router(
    documents.router,
)

# Flashcards
api_router.include_router(
    flashcards.router,
)

# Chat
api_router.include_router(
    chat.router,
)

# AI Tests
api_router.include_router(
    test_ai.router,
)

api_router.include_router(
    test_retriever.router,
)

#Quiz
api_router.include_router(
    quiz.router,
)