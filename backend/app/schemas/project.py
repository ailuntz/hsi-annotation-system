from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """项目公共字段."""

    name: str = Field(min_length=1, max_length=255)
    priority: Literal["normal", "high"] = "normal"
    completion_rate: float = Field(ge=0, le=100, default=0)
    available_samples: int = Field(ge=0, default=0)
    total_samples: int = Field(ge=0, default=0)


class ProjectCreate(ProjectBase):
    """创建项目."""

    data_source_folder: str = Field(min_length=1, max_length=255)


class ProjectUpdate(BaseModel):
    """更新项目."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority: Literal["normal", "high"] | None = None
    completion_rate: float | None = Field(default=None, ge=0, le=100)
    available_samples: int | None = Field(default=None, ge=0)
    total_samples: int | None = Field(default=None, ge=0)


class ProjectResponse(ProjectBase):
    """项目响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime
    created_by: int | None
    updated_by: int | None
    is_archived: bool


class ProjectListResponse(BaseModel):
    """分页响应."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DataSourceInfo(BaseModel):
    """数据源目录."""

    name: str
    total_files: int
    total_samples: int


class DataSourceUploadResponse(BaseModel):
    """上传后返回的目录信息."""

    name: str
    total_files: int


class ProjectExportOptions(BaseModel):
    """项目导出选项."""

    include_project_meta: bool = True
    include_sample_meta: bool = True
    include_annotation_bundle: bool = True


class ProjectExportIncludedSections(BaseModel):
    """导出内容标记."""

    project_meta: bool
    sample_meta: bool
    annotation_bundle: bool
    always: list[str] = Field(default_factory=lambda: ["status", "is_annotated", "last_annotated_by"])


class ProjectExportProjectMeta(BaseModel):
    """导出中的项目信息."""

    project_id: str
    id: int | None = None
    name: str | None = None
    priority: Literal["normal", "high"] | None = None
    completion_rate: float | None = None
    available_samples: int | None = None
    total_samples: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectExportSample(BaseModel):
    """导出样本信息."""

    id: int
    sample_id: str
    sample_type: str
    source_files: list[str]
    status: str
    is_annotated: bool
    last_annotated_by: int | None = None
    created_at: datetime
    updated_at: datetime


class ProjectExportAnnotationDetail(BaseModel):
    """导出标注细节."""

    detail_id: str
    sample_id: str
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


class ProjectExportAnnotationDetailMode(BaseModel):
    """导出显示模式快照."""

    detail_id: str
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


class ProjectExportAnnotationSpectrum(BaseModel):
    """导出光谱曲线."""

    detail_id: str
    position: dict | None = None
    points: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProjectExportAnnotationRecord(BaseModel):
    """单条标注记录（含模式及光谱）."""

    detail: ProjectExportAnnotationDetail
    mode_snapshot: ProjectExportAnnotationDetailMode | None = None
    spectra: list[ProjectExportAnnotationSpectrum] = Field(default_factory=list)


class ProjectExportSampleBlock(BaseModel):
    """每个样本的导出块."""

    sample_id: str
    meta: ProjectExportSample | None = None
    annotations: list[ProjectExportAnnotationRecord] | None = None


class ProjectExportResponse(BaseModel):
    """导出返回."""

    project: ProjectExportProjectMeta
    included_sections: ProjectExportIncludedSections
    generated_at: datetime
    samples: list[ProjectExportSampleBlock] = Field(default_factory=list)
