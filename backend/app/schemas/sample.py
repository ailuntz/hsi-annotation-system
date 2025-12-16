from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnnotationSpectrumResponse(BaseModel):
    """光谱曲线."""

    id: int
    detail_id: int
    position: dict | None = None
    points: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AnnotationDetailModeResponse(BaseModel):
    """标注时的显示模式快照."""

    id: int
    detail_id: int
    r_channel: int
    g_channel: int
    b_channel: int
    r_gain: float
    g_gain: float
    b_gain: float
    gain_algorithm: str
    dark_calibration: bool
    white_calibration: bool
    created_at: datetime
    updated_at: datetime


class AnnotationDetailResponse(BaseModel):
    """标注详情."""

    id: int
    detail_id: str
    sample_id: int
    label_name: str
    color: str
    tool_type: str
    coordinates: dict
    radius: float | None = None
    area: float | None = None
    confidence: float | None = None
    remark: str | None = None
    created_at: datetime
    updated_at: datetime
    mode_snapshot: AnnotationDetailModeResponse | None = None
    spectra: list[AnnotationSpectrumResponse] = Field(default_factory=list)


class AnnotationDetailModeCreate(BaseModel):
    """创建显示模式快照."""

    r_channel: int
    g_channel: int
    b_channel: int
    r_gain: float
    g_gain: float
    b_gain: float
    gain_algorithm: str
    dark_calibration: bool
    white_calibration: bool


class AnnotationSpectrumCreate(BaseModel):
    """创建光谱记录."""

    position: dict | None = None
    points: list[dict] = Field(default_factory=list)


class AnnotationDetailCreate(BaseModel):
    """创建/更新标注详情."""

    label_name: str
    color: str
    tool_type: Literal["rect", "polygon", "point", "circle", "line", "grid"]
    coordinates: dict
    radius: float | None = None
    area: float | None = None
    confidence: float | None = None
    remark: str | None = None
    mode_snapshot: AnnotationDetailModeCreate | None = None
    spectra: list[AnnotationSpectrumCreate] | None = None


class AnnotationSampleBase(BaseModel):
    """样本基础字段."""

    id: int
    sample_id: str
    project_id: int
    sample_type: str
    status: str
    is_annotated: bool
    last_annotated_by: int | None = None
    source_files: list[str]
    created_at: datetime
    updated_at: datetime


class AnnotationSampleSummary(AnnotationSampleBase):
    """样本摘要."""

    has_annotations: bool


class AnnotationSampleDetail(AnnotationSampleBase):
    """样本详情."""

    annotations: list[AnnotationDetailResponse] = Field(default_factory=list)


class SampleListResponse(BaseModel):
    """样本列表."""

    items: list[AnnotationSampleSummary]
    total: int


class SampleStatusUpdate(BaseModel):
    """样本状态更新."""

    status: Literal["valid", "ignored"]
    is_annotated: bool | None = None


class SampleAnnotationsPayload(BaseModel):
    """保存标注载荷."""

    annotations: list[AnnotationDetailCreate] = Field(default_factory=list)
    mark_annotated: bool = True
