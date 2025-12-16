from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import Token
from app.services.user import authenticate_user


async def login(db: AsyncSession, email: str, password: str) -> Token | None:
    """Authenticate user and return access token."""
    user = await authenticate_user(db, email, password)
    if not user:
        return None

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token)
