from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Float, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.annotation_sample import AnnotationSample
    from app.models.annotation_detail_mode import AnnotationDetailMode
    from app.models.annotation_spectrum import AnnotationSpectrum


class AnnotationDetail(Base, TimestampMixin):
    """单条标注细节."""

    __tablename__ = "annotation_details"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    detail_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        default=lambda: uuid4().hex,
    )
    sample_id: Mapped[int] = mapped_column(
        ForeignKey("annotation_samples.id", ondelete="CASCADE"),
        nullable=False,
    )
    label_name: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(16))
    tool_type: Mapped[str] = mapped_column(String(32))
    coordinates: Mapped[dict] = mapped_column(JSON)
    radius: Mapped[float | None] = mapped_column(Float, nullable=True)
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped["AnnotationSample"] = relationship(
        "AnnotationSample",
        back_populates="details",
    )
    mode_snapshot: Mapped["AnnotationDetailMode | None"] = relationship(
        "AnnotationDetailMode",
        back_populates="detail",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    spectra: Mapped[list["AnnotationSpectrum"]] = relationship(
        "AnnotationSpectrum",
        back_populates="detail",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
