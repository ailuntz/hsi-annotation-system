from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TodoBase(BaseModel):
    """Base todo schema."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    priority: int = Field(default=0, ge=0, le=2)


class TodoCreate(TodoBase):
    """Schema for creating a todo."""

    pass


class TodoUpdate(BaseModel):
    """Schema for updating a todo."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=2)


class TodoResponse(TodoBase):
    """Schema for todo response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    completed: bool
    user_id: int
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseModel):
    """Schema for paginated todo list."""

    items: list[TodoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
