from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpectralModeBase(BaseModel):
    """光谱显示模式基础字段."""

    name: str = Field(min_length=1, max_length=255)
    r_channel: int = Field(ge=0, le=10000)
    g_channel: int = Field(ge=0, le=10000)
    b_channel: int = Field(ge=0, le=10000)
    r_gain: float = Field(ge=-4096, le=4096, default=1.0)
    g_gain: float = Field(ge=-4096, le=4096, default=1.0)
    b_gain: float = Field(ge=-4096, le=4096, default=1.0)
    gain_algorithm: str = Field(min_length=1, max_length=100, default="linear")
    dark_calibration: bool = False
    white_calibration: bool = False


class SpectralModeCreate(SpectralModeBase):
    """创建模式."""

    pass


class SpectralModeUpdate(BaseModel):
    """更新模式."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    r_channel: int | None = Field(default=None, ge=0, le=10000)
    g_channel: int | None = Field(default=None, ge=0, le=10000)
    b_channel: int | None = Field(default=None, ge=0, le=10000)
    r_gain: float | None = Field(default=None, ge=-4096, le=4096)
    g_gain: float | None = Field(default=None, ge=-4096, le=4096)
    b_gain: float | None = Field(default=None, ge=-4096, le=4096)
    gain_algorithm: str | None = Field(default=None, min_length=1, max_length=100)
    dark_calibration: bool | None = None
    white_calibration: bool | None = None


class SpectralModeResponse(SpectralModeBase):
    """响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SpectralModeListResponse(BaseModel):
    """分页响应."""

    items: list[SpectralModeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
