from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.project import (
    DataSourceInfo,
    DataSourceUploadResponse,
    ProjectCreate,
    ProjectExportOptions,
    ProjectExportResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project import (
    DATA_SOURCE_ROOT,
    archive_project,
    create_project,
    delete_project,
    export_project_annotations,
    get_project_by_id,
    list_data_sources,
    list_projects,
    restore_project,
    update_project,
)

router = APIRouter()
MAX_UPLOAD_FILES = 5000
MAX_NESTED_DIRS = 3


@router.get("", response_model=ProjectListResponse)
async def list_projects_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    archived: bool | None = None,
) -> ProjectListResponse:
    """项目列表."""
    projects, total = await list_projects(
        db,
        page=page,
        page_size=page_size,
        search=search,
        archived=archived,
    )
    total_pages = (total + page_size - 1) // page_size
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(item) for item in projects],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    project_in: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectResponse:
    """创建项目."""
    project = await create_project(db, project_in, user_id=current_user.id)
    return ProjectResponse.model_validate(project)


@router.get("/data-sources", response_model=list[DataSourceInfo])
async def list_data_sources_endpoint(
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[DataSourceInfo]:
    """列出可选数据源."""
    return list_data_sources()


@router.post("/data-sources/upload-folder", response_model=DataSourceUploadResponse)
async def upload_data_source_folder_endpoint(
    folder_name: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile], File(...)],
    relative_paths: Annotated[list[str], Form(...)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> DataSourceUploadResponse:
    """上传整個文件夹（逐文件）."""
    if not folder_name.strip():
        raise HTTPException(status_code=400, detail="文件夹名称不能为空")
    if not files or not relative_paths:
        raise HTTPException(status_code=400, detail="未提供文件")
    if len(files) != len(relative_paths):
        raise HTTPException(status_code=400, detail="文件与路径数量不一致")
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail="单次上传文件过多")

    safe_folder = folder_name.strip().strip("/").strip()
    safe_folder = safe_folder or f"dataset_{uuid4().hex[:8]}"
    if ".." in safe_folder or "/" in safe_folder or "\\" in safe_folder:
        raise HTTPException(status_code=400, detail="非法文件夹名称")

    target_dir = DATA_SOURCE_ROOT / safe_folder
    if target_dir.exists():
        raise HTTPException(status_code=400, detail="目标文件夹已存在")
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        for upload_file, rel in zip(files, relative_paths):
            rel_path = Path(rel.strip().strip("/"))
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise HTTPException(status_code=400, detail="包含非法路径")
            cleaned_parts = [part for part in rel_path.parts if part and part not in {".", ""}]
            if cleaned_parts and cleaned_parts[0].casefold() == safe_folder.casefold():
                cleaned_parts = cleaned_parts[1:]
            dir_depth = max(len(cleaned_parts) - 1, 0)
            if dir_depth > MAX_NESTED_DIRS:
                raise HTTPException(status_code=400, detail=f"目录嵌套不能超过 {MAX_NESTED_DIRS} 层")
            normalized_rel = Path(*cleaned_parts) if cleaned_parts else Path(upload_file.filename or uuid4().hex)
            destination = target_dir / normalized_rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = await upload_file.read()
            with destination.open("wb") as f:
                f.write(content)
    except Exception as exc:  # pragma: no cover - cleanup on failure
        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    total_files = sum(1 for _ in target_dir.rglob("*") if _.is_file())
    if total_files == 0:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="上传内容为空")

    return DataSourceUploadResponse(name=safe_folder, total_files=total_files)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectResponse:
    """获取单个项目."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: int,
    project_in: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectResponse:
    """更新项目."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    updated = await update_project(db, project, project_in, user_id=current_user.id)
    return ProjectResponse.model_validate(updated)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """删除项目."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    await delete_project(db, project)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project_endpoint(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectResponse:
    """归档项目."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    archived_project = await archive_project(db, project)
    return ProjectResponse.model_validate(archived_project)


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project_endpoint(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectResponse:
    """恢复项目."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    restored = await restore_project(db, project)
    return ProjectResponse.model_validate(restored)


@router.post(
    "/{project_id}/export",
    response_model=ProjectExportResponse,
    status_code=status.HTTP_200_OK,
)
async def export_project_annotations_endpoint(
    project_id: int,
    options: Annotated[ProjectExportOptions, Body(default_factory=ProjectExportOptions)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectExportResponse:
    """导出项目标注."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    payload = await export_project_annotations(db, project, options)
    return payload
