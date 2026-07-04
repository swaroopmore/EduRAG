from fastapi import FastAPI

from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI Teacher using Retrieval-Augmented Generation",
)

app.include_router(api_router)