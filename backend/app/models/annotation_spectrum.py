from __future__ import annotations

from sqlalchemy import Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AnnotationSpectrum(Base, TimestampMixin):
    """光谱曲线数据."""

    __tablename__ = "annotation_spectra"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    detail_id: Mapped[int] = mapped_column(
        ForeignKey("annotation_details.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    points: Mapped[list[dict]] = mapped_column(JSON)

    detail = relationship(
        "AnnotationDetail",
        back_populates="spectra",
    )
