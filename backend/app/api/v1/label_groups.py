from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.label_group import (
    LabelGroupCreate,
    LabelGroupListResponse,
    LabelGroupResponse,
    LabelGroupUpdate,
)
from app.services.label_group import (
    create_label_group,
    delete_label_group,
    get_label_group_by_id,
    list_label_groups,
    update_label_group,
)

router = APIRouter()


@router.get("", response_model=LabelGroupListResponse)
async def list_label_groups_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=255),
) -> LabelGroupListResponse:
    """标注组列表."""
    groups, total = await list_label_groups(
        db,
        page=page,
        page_size=page_size,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size
    return LabelGroupListResponse(
        items=[LabelGroupResponse.model_validate(group) for group in groups],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=LabelGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_label_group_endpoint(
    group_in: LabelGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> LabelGroupResponse:
    """创建标注组."""
    group = await create_label_group(db, group_in, created_by=current_user.id)
    return LabelGroupResponse.model_validate(group)


@router.get("/{group_id}", response_model=LabelGroupResponse)
async def get_label_group_endpoint(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> LabelGroupResponse:
    """获取标注组详情."""
    group = await get_label_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标注组不存在")
    return LabelGroupResponse.model_validate(group)


@router.patch("/{group_id}", response_model=LabelGroupResponse)
async def update_label_group_endpoint(
    group_id: int,
    group_in: LabelGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> LabelGroupResponse:
    """更新标注组."""
    group = await get_label_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标注组不存在")
    updated = await update_label_group(db, group, group_in)
    return LabelGroupResponse.model_validate(updated)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label_group_endpoint(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """删除标注组."""
    group = await get_label_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标注组不存在")
    await delete_label_group(db, group)
