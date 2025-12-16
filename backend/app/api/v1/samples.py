from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.sample import (
    AnnotationSampleDetail,
    SampleAnnotationsPayload,
    SampleListResponse,
    SampleStatusUpdate,
)
from app.services.sample import (
    build_sample_asset_path,
    get_sample_detail,
    list_samples_for_project,
    replace_annotations,
    update_sample_status,
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/samples",
    response_model=SampleListResponse,
)
async def list_project_samples_endpoint(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> SampleListResponse:
    """项目下样本列表."""
    return await list_samples_for_project(db, project_id)


@router.get("/samples/{sample_id}", response_model=AnnotationSampleDetail)
async def get_sample_detail_endpoint(
    sample_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> AnnotationSampleDetail:
    """样本详情."""
    return await get_sample_detail(db, sample_id)


@router.patch("/samples/{sample_id}", response_model=AnnotationSampleDetail)
async def update_sample_status_endpoint(
    sample_id: int,
    payload: SampleStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> AnnotationSampleDetail:
    """更新样本状态."""
    return await update_sample_status(db, sample_id, payload)


@router.put("/samples/{sample_id}/annotations", response_model=AnnotationSampleDetail)
async def replace_sample_annotations_endpoint(
    sample_id: int,
    payload: SampleAnnotationsPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AnnotationSampleDetail:
    """保存样本标注."""
    return await replace_annotations(db, sample_id, payload, user_id=current_user.id)


@router.get("/samples/{sample_id}/assets")
async def get_sample_asset_endpoint(
    sample_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
    path: str = Query(..., description="样本相对路径"),
) -> Response:
    """下载样本文件."""
    sample = await get_sample_detail(db, sample_id)
    file_path = build_sample_asset_path(sample, path)
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=Path(path).name,
    )
