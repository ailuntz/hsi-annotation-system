from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LabelCategoryBase(BaseModel):
    """标签种类公共字段."""

    name: str = Field(min_length=1, max_length=100)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="十六进制颜色")
    order_index: int | None = Field(default=None, ge=0)


class LabelCategoryResponse(LabelCategoryBase):
    """标签种类响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_index: int | None


class LabelGroupBase(BaseModel):
    """标注组公共字段."""

    name: str = Field(min_length=1, max_length=255)


class LabelGroupCreate(LabelGroupBase):
    """创建标注组."""

    labels: list[LabelCategoryBase] = Field(default_factory=list)


class LabelGroupUpdate(BaseModel):
    """更新标注组."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    labels: list[LabelCategoryBase] | None = None


class LabelGroupResponse(LabelGroupBase):
    """标注组响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    labels: list[LabelCategoryResponse]


class LabelGroupListResponse(BaseModel):
    """标注组列表响应."""

    items: list[LabelGroupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
