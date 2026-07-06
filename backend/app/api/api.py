from fastapi import APIRouter
from app.api.routes import health,database
from app.api.routes import auth
from app.api.routes import subject
from app.api.routes import documents
from app.api.routes import chat
from app.api.routes import test_ai
from app.api.routes import test_retriever
from app.api.routes import chat

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(database.router, tags=["Database"])

api_router.include_router(auth.router)

api_router.include_router(subject.router)

api_router.include_router(documents.router)

api_router.include_router(test_retriever.router)


api_router.include_router(chat.router)

api_router.include_router(test_ai.router)