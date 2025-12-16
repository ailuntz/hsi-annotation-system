from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.display_algorithm import DisplayAlgorithm


class AnnotationDetailMode(Base, TimestampMixin):
    """标注时的显示模式快照."""

    __tablename__ = "annotation_detail_modes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    detail_id: Mapped[int] = mapped_column(
        ForeignKey("annotation_details.id", ondelete="CASCADE"),
        nullable=False,
    )
    r_channel: Mapped[int] = mapped_column(Integer)
    g_channel: Mapped[int] = mapped_column(Integer)
    b_channel: Mapped[int] = mapped_column(Integer)
    r_gain: Mapped[float] = mapped_column(Float, default=1.0)
    g_gain: Mapped[float] = mapped_column(Float, default=1.0)
    b_gain: Mapped[float] = mapped_column(Float, default=1.0)
    gain_algorithm_id: Mapped[int] = mapped_column(
        ForeignKey("display_algorithms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dark_calibration: Mapped[bool] = mapped_column(Boolean, default=False)
    white_calibration: Mapped[bool] = mapped_column(Boolean, default=False)

    detail = relationship(
        "AnnotationDetail",
        back_populates="mode_snapshot",
    )
    algorithm = relationship("DisplayAlgorithm", lazy="joined")

    @property
    def gain_algorithm(self) -> str:
        return self.algorithm.code if self.algorithm else "linear"
