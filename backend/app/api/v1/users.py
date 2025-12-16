import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import update_user

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Magic bytes (文件签名) 用于验证真实文件类型
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",  # JPEG
    b"\x89PNG\r\n\x1a\n": "image/png",  # PNG
    b"GIF87a": "image/gif",  # GIF87a
    b"GIF89a": "image/gif",  # GIF89a
    b"RIFF": "image/webp",  # WebP (需要进一步检查)
}


def validate_image_content(content: bytes) -> bool:
    """验证文件内容是否为有效的图片格式"""
    # 检查常见图片格式的 magic bytes
    if content[:3] == b"\xff\xd8\xff":  # JPEG
        return True
    if content[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
        return True
    if content[:6] in (b"GIF87a", b"GIF89a"):  # GIF
        return True
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":  # WebP
        return True
    return False


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Update current user."""
    user = await update_user(db, current_user, user_in)
    return UserResponse.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Delete current user (soft delete by setting is_active to False)."""
    current_user.is_active = False
    await db.commit()


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Upload user avatar."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB")

    # 验证文件内容是否为真实图片（防止恶意文件伪装）
    if not validate_image_content(content):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. The file content does not match a valid image format.",
        )

    # Delete old avatar if exists
    if current_user.avatar:
        old_path = UPLOAD_DIR / current_user.avatar.split("/")[-1]
        if old_path.exists():
            old_path.unlink()

    # Save new avatar
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Update user avatar URL
    current_user.avatar = f"/api/v1/users/avatar/{filename}"
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.get("/avatar/{filename}")
async def get_avatar(filename: str) -> FileResponse:
    """Get avatar file."""
    # 安全验证：防止路径遍历攻击
    # 1. 确保文件名不包含路径分隔符
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = UPLOAD_DIR / filename

    # 2. 确保解析后的路径在 UPLOAD_DIR 内
    try:
        filepath.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath)
