from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.display_algorithm import DisplayAlgorithm

if TYPE_CHECKING:
    from app.models.user import User


class SpectralDisplayMode(Base, TimestampMixin):
    """预置光谱显示模式."""

    __tablename__ = "spectral_display_modes"
    __table_args__ = (
        CheckConstraint("r_gain BETWEEN -4096 AND 4096", name="ck_spectral_modes_r_gain"),
        CheckConstraint("g_gain BETWEEN -4096 AND 4096", name="ck_spectral_modes_g_gain"),
        CheckConstraint("b_gain BETWEEN -4096 AND 4096", name="ck_spectral_modes_b_gain"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
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
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator: Mapped["User | None"] = relationship("User")
    algorithm: Mapped[DisplayAlgorithm] = relationship("DisplayAlgorithm", lazy="joined")

    @property
    def gain_algorithm(self) -> str:
        return self.algorithm.code if self.algorithm else "linear"
