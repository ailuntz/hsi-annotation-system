from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class LabelGroup(Base, TimestampMixin):
    """预置标注组."""

    __tablename__ = "label_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    labels: Mapped[list["LabelCategory"]] = relationship(
        "LabelCategory",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="LabelCategory.order_index",
    )
    creator: Mapped["User | None"] = relationship("User")


class LabelCategory(Base):
    """标注组内的标签定义."""

    __tablename__ = "label_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("label_groups.id", ondelete="CASCADE"),
    )

    group: Mapped["LabelGroup"] = relationship("LabelGroup", back_populates="labels")
