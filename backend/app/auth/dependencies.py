from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.repositories.user_repository import UserRepository

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        print("=" * 50)
        print(payload)

        user_id = payload.get("sub")

        print("USER ID:", user_id)

        repository = UserRepository(db)

        user = repository.get_by_id(user_id)

        print("USER:", user)
        print("=" * 50)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return user

    except JWTError as e:
        print(e)
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )