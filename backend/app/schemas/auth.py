from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str | None = None
    exp: int | None = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: str
    password: str
