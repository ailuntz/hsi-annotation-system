from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.annotation_detail import AnnotationDetail


class AnnotationSample(Base, TimestampMixin):
    """标注样本（标注模型）."""

    __tablename__ = "annotation_samples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("annotation_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    sample_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        default=lambda: uuid4().hex,
    )
    sample_type: Mapped[str] = mapped_column(String(32))  # image / hyperspectral
    source_files: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="valid")
    is_annotated: Mapped[bool] = mapped_column(Boolean, default=False)
    last_annotated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    project = relationship(
        "AnnotationProject",
        backref=backref(
            "samples",
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )
    details: Mapped[list["AnnotationDetail"]] = relationship(
        "AnnotationDetail",
        back_populates="sample",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
