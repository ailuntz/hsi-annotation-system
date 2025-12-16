from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.rate_limit import auth_rate_limiter
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import login
from app.services.user import create_user, get_user_by_email

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """OAuth2 compatible token login."""
    # 检查速率限制
    auth_rate_limiter.check(request)

    token = await login(db, form_data.username, form_data.password)
    if not token:
        # 记录失败尝试
        auth_rate_limiter.record_attempt(request, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",  # 使用通用错误信息，不泄露账户存在
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 记录成功登录，清除限制
    auth_rate_limiter.record_attempt(request, success=True)
    return token


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new user."""
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user = await create_user(db, user_in)
    return UserResponse.model_validate(user)
