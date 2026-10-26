from fastapi import APIRouter

from app.api.routes import (
    auth,
    chat,
    dashboard,
    documents,
    flashcards,
    health,
    notes,
    quiz,
    study_plan,
    subject,
)

api_router = APIRouter()

for module in (
    health,
    auth,
    dashboard,
    subject,
    documents,
    flashcards,
    chat,
    quiz,
    notes,
    study_plan,
):
    api_router.include_router(module.router)
