from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.label_group import LabelCategory, LabelGroup
from app.schemas.label_group import (
    LabelCategoryBase,
    LabelGroupCreate,
    LabelGroupUpdate,
)


async def list_label_groups(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
) -> tuple[list[LabelGroup], int]:
    """分页获取标注组."""
    filters: list = []
    if search:
        like = f"%{search.lower()}%"
        filters.append(func.lower(LabelGroup.name).like(like))

    count_query = select(func.count()).select_from(LabelGroup)
    if filters:
        count_query = count_query.where(*filters)
    total = await db.scalar(count_query) or 0

    query = (
        select(LabelGroup)
        .options(selectinload(LabelGroup.labels))
        .order_by(LabelGroup.created_at.desc())
    )
    if filters:
        query = query.where(*filters)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    groups = list(result.scalars().unique().all())
    return groups, total


async def get_label_group_by_id(db: AsyncSession, group_id: int) -> LabelGroup | None:
    """根据 ID 获取标注组."""
    result = await db.execute(
        select(LabelGroup)
            .options(selectinload(LabelGroup.labels))
            .where(LabelGroup.id == group_id)
    )
    return result.unique().scalar_one_or_none()


def _build_label_entities(
    labels: Sequence[LabelCategoryBase],
) -> list[LabelCategory]:
    entities: list[LabelCategory] = []
    for idx, label in enumerate(labels):
        order_index = label.order_index if label.order_index is not None else idx
        entities.append(
            LabelCategory(
                name=label.name,
                color=label.color,
                order_index=order_index,
            )
        )
    return entities


async def create_label_group(
    db: AsyncSession,
    group_in: LabelGroupCreate,
    *,
    created_by: int | None = None,
) -> LabelGroup:
    """创建标注组."""
    group = LabelGroup(name=group_in.name, created_by=created_by)
    group.labels = _build_label_entities(group_in.labels)
    db.add(group)
    await db.flush()
    await db.refresh(group)
    await db.refresh(group, attribute_names=["labels"])
    return group


async def update_label_group(
    db: AsyncSession,
    group: LabelGroup,
    group_in: LabelGroupUpdate,
) -> LabelGroup:
    """更新标注组."""
    if group_in.name is not None:
        group.name = group_in.name

    if group_in.labels is not None:
        group.labels.clear()
        group.labels.extend(_build_label_entities(group_in.labels))

    await db.flush()
    await db.refresh(group)
    await db.refresh(group, attribute_names=["labels"])
    return group


async def delete_label_group(db: AsyncSession, group: LabelGroup) -> None:
    """删除标注组."""
    await db.delete(group)
    await db.commit()
