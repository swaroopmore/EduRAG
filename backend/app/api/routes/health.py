from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "Welcome to EduRAG API",
        "status": "running"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy"
    }