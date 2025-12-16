from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AnnotationProject(Base, TimestampMixin):
    """标注项目模型."""

    __tablename__ = "annotation_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        default=lambda: uuid4().hex,
    )
    name: Mapped[str] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    available_samples: Mapped[int] = mapped_column(Integer, default=0)
    total_samples: Mapped[int] = mapped_column(Integer, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    updater: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[updated_by],
    )
