from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.annotation_detail import AnnotationDetail
from app.models.annotation_detail_mode import AnnotationDetailMode
from app.models.annotation_sample import AnnotationSample
from app.models.annotation_spectrum import AnnotationSpectrum
from app.models.project import AnnotationProject
from app.schemas.project import (
    DataSourceInfo,
    ProjectCreate,
    ProjectExportAnnotationDetail,
    ProjectExportAnnotationDetailMode,
    ProjectExportAnnotationRecord,
    ProjectExportAnnotationSpectrum,
    ProjectExportIncludedSections,
    ProjectExportOptions,
    ProjectExportProjectMeta,
    ProjectExportResponse,
    ProjectExportSample,
    ProjectExportSampleBlock,
    ProjectUpdate,
)

DATA_SOURCE_ROOT = Path(__file__).parent.parent.parent / "uploads" / "datasource"
DATA_SOURCE_ROOT.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
HYPER_EXTS = {".spe", ".hdr", ".figspecblack", ".figspecwhite"}


def _ensure_within_root(path: Path) -> None:
    """Ensure the resolved path is within datasource root."""
    try:
        path.resolve().relative_to(DATA_SOURCE_ROOT.resolve())
    except ValueError as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=400, detail="非法数据源路径") from exc


def list_data_sources() -> list[DataSourceInfo]:
    """列出数据源文件夹."""
    sources: list[DataSourceInfo] = []
    for entry in DATA_SOURCE_ROOT.iterdir():
        if not entry.is_dir():
            continue
        total_files = sum(1 for _ in entry.rglob("*") if _.is_file())
        total_samples = estimate_samples(entry)
        sources.append(
            DataSourceInfo(
                name=entry.name,
                total_files=total_files,
                total_samples=total_samples,
            )
        )
    return sorted(sources, key=lambda x: x.name)


def estimate_samples(folder: Path) -> int:
    """估算目录中的样本数量."""
    images = 0
    hyper_groups: set[tuple[str, str]] = set()
    for file in folder.rglob("*"):
        if not file.is_file():
            continue
        ext = file.suffix.lower()
        if ext in IMAGE_EXTS:
            images += 1
        elif ext in HYPER_EXTS:
            rel = file.relative_to(folder)
            hyper_groups.add((str(rel.parent), rel.stem))
    return images + len(hyper_groups)


def validate_data_source_folder(folder_name: str) -> Path:
    """验证数据源目录是否存在."""
    folder = DATA_SOURCE_ROOT / folder_name
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="数据源不存在")
    _ensure_within_root(folder)
    return folder


def parse_samples_from_folder(folder: Path) -> list[dict]:
    """从目录解析样本信息."""
    samples: list[dict] = []
    hyper_map: dict[tuple[str, str], list[str]] = defaultdict(list)
    base = folder.name

    for file in folder.rglob("*"):
        if not file.is_file():
            continue
        rel = file.relative_to(folder)
        ext = file.suffix.lower()
        if ext in IMAGE_EXTS:
            samples.append(
                {
                    "sample_type": "image",
                    "files": [str(Path(base) / rel)],
                }
            )
        elif ext in HYPER_EXTS:
            key = (str(rel.parent), rel.stem)
            hyper_map[key].append(str(rel))

    for (_parent, _stem), files in hyper_map.items():
        has_spe = any(Path(path).suffix.lower() == ".spe" for path in files)
        has_hdr = any(Path(path).suffix.lower() == ".hdr" for path in files)
        if not (has_spe and has_hdr):
            continue
        samples.append(
            {
                "sample_type": "hyperspectral",
                "files": [str(Path(base) / Path(f)) for f in files],
            }
        )

    return samples


async def list_projects(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    archived: bool | None = None,
) -> tuple[list[AnnotationProject], int]:
    """分页项目."""
    filters: list = []
    if search:
        like = f"%{search.lower()}%"
        filters.append(func.lower(AnnotationProject.name).like(like))
    if archived is not None:
        filters.append(AnnotationProject.is_archived.is_(archived))

    count_query = select(func.count()).select_from(AnnotationProject)
    if filters:
        count_query = count_query.where(*filters)
    total = await db.scalar(count_query) or 0

    query = (
        select(AnnotationProject)
        .order_by(AnnotationProject.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    return list(result.scalars().unique().all()), total


async def get_project_by_id(
    db: AsyncSession,
    project_id: int,
) -> AnnotationProject | None:
    """获取项目."""
    result = await db.execute(
        select(AnnotationProject).where(AnnotationProject.id == project_id)
    )
    return result.unique().scalar_one_or_none()


async def create_project(
    db: AsyncSession,
    project_in: ProjectCreate,
    *,
    user_id: int | None,
) -> AnnotationProject:
    """创建项目并导入数据源."""
    folder = validate_data_source_folder(project_in.data_source_folder)
    samples_payload = parse_samples_from_folder(folder)
    if not samples_payload:
        raise HTTPException(status_code=400, detail="数据源中没有可用样本")

    project = AnnotationProject(
        name=project_in.name,
        priority=project_in.priority,
        completion_rate=0.0,
        available_samples=len(samples_payload),
        total_samples=len(samples_payload),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(project)
    await db.flush()
    await create_samples(db, project.id, samples_payload)
    await db.refresh(project)
    return project


async def create_samples(
    db: AsyncSession,
    project_id: int,
    samples_payload: Iterable[dict],
) -> None:
    """批量创建样本记录."""
    for item in samples_payload:
        sample = AnnotationSample(
            project_id=project_id,
            sample_type=item["sample_type"],
            source_files=item["files"],
            status="valid",
            is_annotated=False,
        )
        db.add(sample)
    await db.flush()


async def update_project(
    db: AsyncSession,
    project: AnnotationProject,
    project_in: ProjectUpdate,
    *,
    user_id: int | None,
) -> AnnotationProject:
    """更新项目."""
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    project.updated_by = user_id
    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: AnnotationProject) -> None:
    """删除项目."""
    await db.delete(project)


async def refresh_project_statistics(db: AsyncSession, project_id: int) -> None:
    """刷新项目统计信息."""
    total_query = select(func.count(AnnotationSample.id)).where(
        AnnotationSample.project_id == project_id
    )
    annotated_query = select(func.count(AnnotationSample.id)).where(
        AnnotationSample.project_id == project_id,
        AnnotationSample.is_annotated.is_(True),
    )
    available_query = select(func.count(AnnotationSample.id)).where(
        AnnotationSample.project_id == project_id,
        AnnotationSample.status != "ignored",
    )

    total = await db.scalar(total_query) or 0
    annotated = await db.scalar(annotated_query) or 0
    available = await db.scalar(available_query) or 0

    project = await db.get(AnnotationProject, project_id)
    if not project:
        return

    project.total_samples = total
    project.available_samples = available
    project.completion_rate = (
        round((annotated / total) * 100, 2) if total > 0 else 0.0
    )
    await db.flush()
    await db.commit()


async def archive_project(
    db: AsyncSession,
    project: AnnotationProject,
) -> AnnotationProject:
    """归档项目."""
    project.is_archived = True
    project.priority = "normal"
    await db.flush()
    await db.refresh(project)
    return project


async def restore_project(
    db: AsyncSession,
    project: AnnotationProject,
) -> AnnotationProject:
    """恢复项目."""
    project.is_archived = False
    await db.flush()
    await db.refresh(project)
    return project


async def export_project_annotations(
    db: AsyncSession,
    project: AnnotationProject,
    options: ProjectExportOptions,
) -> ProjectExportResponse:
    """导出项目标注."""

    included_sections = ProjectExportIncludedSections(
        project_meta=options.include_project_meta,
        sample_meta=options.include_sample_meta,
        annotation_bundle=options.include_annotation_bundle,
    )

    project_block = ProjectExportProjectMeta(project_id=project.project_id)
    if options.include_project_meta:
        project_block.id = project.id
        project_block.name = project.name
        project_block.priority = project.priority  # type: ignore[assignment]
        project_block.completion_rate = project.completion_rate
        project_block.available_samples = project.available_samples
        project_block.total_samples = project.total_samples
        project_block.created_at = project.created_at
        project_block.updated_at = project.updated_at

    samples: list[AnnotationSample] = []
    if options.include_sample_meta or options.include_annotation_bundle:
        sample_stmt = (
            select(AnnotationSample)
            .where(AnnotationSample.project_id == project.id)
            .options(
                selectinload(AnnotationSample.details)
                .selectinload(AnnotationDetail.spectra),
                selectinload(AnnotationSample.details)
                .selectinload(AnnotationDetail.mode_snapshot)
                .joinedload(AnnotationDetailMode.algorithm),
            )
            .order_by(AnnotationSample.id.asc())
        )
        result = await db.execute(sample_stmt)
        samples = list(result.scalars().unique().all())

    sample_blocks: list[ProjectExportSampleBlock] = []
    if samples:
        for sample in samples:
            meta_payload: ProjectExportSample | None = None
            if options.include_sample_meta:
                meta_payload = ProjectExportSample(
                    id=sample.id,
                    sample_id=sample.sample_id,
                    sample_type=sample.sample_type,
                    source_files=sample.source_files,
                    status=sample.status,
                    is_annotated=sample.is_annotated,
                    last_annotated_by=sample.last_annotated_by,
                    created_at=sample.created_at,
                    updated_at=sample.updated_at,
                )

            annotations_payload: list[ProjectExportAnnotationRecord] | None = None
            if options.include_annotation_bundle:
                annotations_payload = []
                for detail in sample.details:
                    detail_payload = ProjectExportAnnotationDetail(
                        detail_id=detail.detail_id,
                        sample_id=sample.sample_id,
                        label_name=detail.label_name,
                        color=detail.color,
                        tool_type=detail.tool_type,
                        coordinates=detail.coordinates,
                        radius=detail.radius,
                        area=detail.area,
                        confidence=detail.confidence,
                        remark=detail.remark,
                        created_at=detail.created_at,
                        updated_at=detail.updated_at,
                    )
                    mode_payload = None
                    if (
                        sample.sample_type == "hyperspectral"
                        and detail.mode_snapshot is not None
                    ):
                        snapshot = detail.mode_snapshot
                        mode_payload = ProjectExportAnnotationDetailMode(
                            detail_id=detail.detail_id,
                            r_channel=snapshot.r_channel,
                            g_channel=snapshot.g_channel,
                            b_channel=snapshot.b_channel,
                            r_gain=snapshot.r_gain,
                            g_gain=snapshot.g_gain,
                            b_gain=snapshot.b_gain,
                            gain_algorithm=snapshot.gain_algorithm,
                            dark_calibration=snapshot.dark_calibration,
                            white_calibration=snapshot.white_calibration,
                            created_at=snapshot.created_at,
                            updated_at=snapshot.updated_at,
                        )

                    spectra_payload: list[ProjectExportAnnotationSpectrum] = []
                    if sample.sample_type == "hyperspectral":
                        for spectrum in detail.spectra:
                            spectra_payload.append(
                                ProjectExportAnnotationSpectrum(
                                    detail_id=detail.detail_id,
                                    position=spectrum.position,
                                    points=spectrum.points,
                                    created_at=spectrum.created_at,
                                    updated_at=spectrum.updated_at,
                                )
                            )

                    annotations_payload.append(
                        ProjectExportAnnotationRecord(
                            detail=detail_payload,
                            mode_snapshot=mode_payload,
                            spectra=spectra_payload,
                        )
                    )

            sample_blocks.append(
                ProjectExportSampleBlock(
                    sample_id=sample.sample_id,
                    meta=meta_payload,
                    annotations=annotations_payload,
                )
            )

    return ProjectExportResponse(
        project=project_block,
        included_sections=included_sections,
        generated_at=datetime.now(timezone.utc),
        samples=sample_blocks,
    )
