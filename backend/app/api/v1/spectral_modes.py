from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.spectral_mode import (
    SpectralModeCreate,
    SpectralModeListResponse,
    SpectralModeResponse,
    SpectralModeUpdate,
)
from app.services.spectral_mode import (
    create_spectral_mode,
    delete_spectral_mode,
    get_spectral_mode_by_id,
    list_spectral_modes,
    update_spectral_mode,
)

router = APIRouter()


@router.get("", response_model=SpectralModeListResponse)
async def list_spectral_modes_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=255),
) -> SpectralModeListResponse:
    """分页光谱模式."""
    modes, total = await list_spectral_modes(
        db,
        page=page,
        page_size=page_size,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size
    return SpectralModeListResponse(
        items=[SpectralModeResponse.model_validate(mode) for mode in modes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=SpectralModeResponse, status_code=status.HTTP_201_CREATED)
async def create_spectral_mode_endpoint(
    mode_in: SpectralModeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SpectralModeResponse:
    """创建模式."""
    mode = await create_spectral_mode(db, mode_in, created_by=current_user.id)
    return SpectralModeResponse.model_validate(mode)


@router.get("/{mode_id}", response_model=SpectralModeResponse)
async def get_spectral_mode_endpoint(
    mode_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> SpectralModeResponse:
    """获取模式."""
    mode = await get_spectral_mode_by_id(db, mode_id)
    if not mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模式不存在")
    return SpectralModeResponse.model_validate(mode)


@router.patch("/{mode_id}", response_model=SpectralModeResponse)
async def update_spectral_mode_endpoint(
    mode_id: int,
    mode_in: SpectralModeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SpectralModeResponse:
    """更新模式."""
    mode = await get_spectral_mode_by_id(db, mode_id)
    if not mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模式不存在")
    updated = await update_spectral_mode(db, mode, mode_in)
    return SpectralModeResponse.model_validate(updated)


@router.delete("/{mode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spectral_mode_endpoint(
    mode_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """删除模式."""
    mode = await get_spectral_mode_by_id(db, mode_id)
    if not mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模式不存在")
    await delete_spectral_mode(db, mode)
