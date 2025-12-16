from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.display_algorithm import DisplayAlgorithm

DEFAULT_ALGORITHM_CODE = "linear"


async def list_display_algorithms(db: AsyncSession) -> Sequence[DisplayAlgorithm]:
    query = select(DisplayAlgorithm).order_by(DisplayAlgorithm.id.asc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_display_algorithm_by_code(
    db: AsyncSession,
    code: str | None,
) -> DisplayAlgorithm:
    normalized = (code or DEFAULT_ALGORITHM_CODE).strip()
    query = select(DisplayAlgorithm).where(DisplayAlgorithm.code == normalized)
    result = await db.execute(query)
    algo = result.scalar_one_or_none()
    if algo:
        return algo
    fallback_query = select(DisplayAlgorithm).where(DisplayAlgorithm.code == DEFAULT_ALGORITHM_CODE)
    fallback_result = await db.execute(fallback_query)
    fallback = fallback_result.scalar_one()
    return fallback
