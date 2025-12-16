from __future__ import annotations

from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation_detail import AnnotationDetail
from app.models.annotation_detail_mode import AnnotationDetailMode
from app.models.annotation_sample import AnnotationSample
from app.models.annotation_spectrum import AnnotationSpectrum
from app.schemas.sample import (
    AnnotationDetailCreate,
    AnnotationDetailModeCreate,
    AnnotationDetailModeResponse,
    AnnotationDetailResponse,
    AnnotationSampleDetail,
    AnnotationSampleSummary,
    AnnotationSpectrumResponse,
    SampleAnnotationsPayload,
    SampleListResponse,
    SampleStatusUpdate,
)
from app.services.display_algorithm import get_display_algorithm_by_code
from app.services.project import DATA_SOURCE_ROOT, refresh_project_statistics


def _ensure_sample_asset(path: Path) -> None:
    real_root = DATA_SOURCE_ROOT.resolve()
    try:
        path.resolve().relative_to(real_root)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法文件路径") from exc


async def list_samples_for_project(
    db: AsyncSession,
    project_id: int,
) -> SampleListResponse:
    query = (
        select(AnnotationSample)
        .where(AnnotationSample.project_id == project_id)
        .order_by(AnnotationSample.id.asc())
    )
    result = await db.execute(query)
    samples = result.scalars().all()
    items = [
        AnnotationSampleSummary(
            id=sample.id,
            sample_id=sample.sample_id,
            project_id=sample.project_id,
            sample_type=sample.sample_type,
            status=sample.status,
            is_annotated=sample.is_annotated,
            last_annotated_by=sample.last_annotated_by,
            source_files=sample.source_files,
            created_at=sample.created_at,
            updated_at=sample.updated_at,
            has_annotations=sample.is_annotated,
        )
        for sample in samples
    ]
    return SampleListResponse(items=items, total=len(items))


async def get_sample_detail(
    db: AsyncSession,
    sample_id: int,
) -> AnnotationSampleDetail:
    query = (
        select(AnnotationSample)
        .options(
            selectinload(AnnotationSample.details)
            .selectinload(AnnotationDetail.mode_snapshot)
            .selectinload(AnnotationDetailMode.algorithm)
        )
        .options(
            selectinload(AnnotationSample.details)
            .selectinload(AnnotationDetail.spectra)
        )
        .where(AnnotationSample.id == sample_id)
    )
    result = await db.execute(query)
    sample = result.unique().scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="样本不存在")

    def _serialize_detail(detail: AnnotationDetail) -> AnnotationDetailResponse:
        mode_snapshot = None
        if detail.mode_snapshot:
            snapshot = detail.mode_snapshot
            mode_snapshot = AnnotationDetailModeResponse(
                id=snapshot.id,
                detail_id=snapshot.detail_id,
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

        spectra = [
            AnnotationSpectrumResponse(
                id=spectrum.id,
                detail_id=spectrum.detail_id,
                position=spectrum.position,
                points=spectrum.points or [],
                created_at=spectrum.created_at,
                updated_at=spectrum.updated_at,
            )
            for spectrum in detail.spectra
        ]

        return AnnotationDetailResponse(
            id=detail.id,
            detail_id=detail.detail_id,
            sample_id=detail.sample_id,
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
            mode_snapshot=mode_snapshot,
            spectra=spectra,
        )

    annotations = [_serialize_detail(detail) for detail in sample.details]

    return AnnotationSampleDetail(
        id=sample.id,
        sample_id=sample.sample_id,
        project_id=sample.project_id,
        sample_type=sample.sample_type,
        status=sample.status,
        is_annotated=sample.is_annotated,
        last_annotated_by=sample.last_annotated_by,
        source_files=sample.source_files,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        annotations=annotations,
    )


async def update_sample_status(
    db: AsyncSession,
    sample_id: int,
    payload: SampleStatusUpdate,
) -> AnnotationSampleDetail:
    sample_query = select(AnnotationSample).where(AnnotationSample.id == sample_id)
    result = await db.execute(sample_query)
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="样本不存在")

    sample.status = payload.status
    if payload.is_annotated is not None:
        sample.is_annotated = payload.is_annotated

    await db.flush()
    await refresh_project_statistics(db, sample.project_id)
    return await get_sample_detail(db, sample_id)


async def replace_annotations(
    db: AsyncSession,
    sample_id: int,
    payload: SampleAnnotationsPayload,
    *,
    user_id: int | None,
) -> AnnotationSampleDetail:
    sample_query = (
        select(AnnotationSample)
        .options(selectinload(AnnotationSample.details))
        .where(AnnotationSample.id == sample_id)
    )
    result = await db.execute(sample_query)
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="样本不存在")

    for detail in list(sample.details):
        await db.delete(detail)

    await db.flush()

    algorithm_cache: dict[str, int] = {}

    for detail_payload in payload.annotations:
        detail = AnnotationDetail(
            sample_id=sample.id,
            label_name=detail_payload.label_name,
            color=detail_payload.color,
            tool_type=detail_payload.tool_type,
            coordinates=detail_payload.coordinates,
            radius=detail_payload.radius,
            area=detail_payload.area,
            confidence=detail_payload.confidence,
            remark=detail_payload.remark,
        )
        db.add(detail)
        await db.flush()

        if detail_payload.mode_snapshot:
            algorithm_code = detail_payload.mode_snapshot.gain_algorithm
            if algorithm_code not in algorithm_cache:
                algorithm = await get_display_algorithm_by_code(db, algorithm_code)
                algorithm_cache[algorithm_code] = algorithm.id
            algorithm_id = algorithm_cache[algorithm_code]
            db.add(
                AnnotationDetailMode(
                    detail_id=detail.id,
                    r_channel=detail_payload.mode_snapshot.r_channel,
                    g_channel=detail_payload.mode_snapshot.g_channel,
                    b_channel=detail_payload.mode_snapshot.b_channel,
                    r_gain=detail_payload.mode_snapshot.r_gain,
                    g_gain=detail_payload.mode_snapshot.g_gain,
                    b_gain=detail_payload.mode_snapshot.b_gain,
                    gain_algorithm_id=algorithm_id,
                    dark_calibration=detail_payload.mode_snapshot.dark_calibration,
                    white_calibration=detail_payload.mode_snapshot.white_calibration,
                )
            )

        for spectrum_payload in detail_payload.spectra or []:
            db.add(
                AnnotationSpectrum(
                    detail_id=detail.id,
                    position=spectrum_payload.position,
                    points=spectrum_payload.points,
                )
            )

    sample.is_annotated = payload.mark_annotated and bool(payload.annotations)
    sample.last_annotated_by = user_id
    await db.flush()
    await refresh_project_statistics(db, sample.project_id)
    db.expire_all()
    return await get_sample_detail(db, sample_id)


def build_sample_asset_path(sample: AnnotationSample | AnnotationSampleDetail, relative: str) -> Path:
    """样本文件路径."""
    if relative not in sample.source_files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    path = DATA_SOURCE_ROOT / relative
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    _ensure_sample_asset(path)
    return path
