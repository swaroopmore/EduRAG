from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter()


@router.get("/database-test")
def database_test(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "Database Connected Successfully"
    }