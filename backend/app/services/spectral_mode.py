from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spectral_mode import SpectralDisplayMode
from app.schemas.spectral_mode import SpectralModeCreate, SpectralModeUpdate
from app.services.display_algorithm import get_display_algorithm_by_code


async def list_spectral_modes(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
) -> tuple[list[SpectralDisplayMode], int]:
    """分页列出光谱模式."""
    filters: list = []
    if search:
        like = f"%{search.lower()}%"
        filters.append(func.lower(SpectralDisplayMode.name).like(like))

    count_query = select(func.count()).select_from(SpectralDisplayMode)
    if filters:
        count_query = count_query.where(*filters)
    total = await db.scalar(count_query) or 0

    query = select(SpectralDisplayMode).order_by(SpectralDisplayMode.created_at.desc())
    if filters:
        query = query.where(*filters)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_spectral_mode_by_id(
    db: AsyncSession,
    mode_id: int,
) -> SpectralDisplayMode | None:
    """获取单个模式."""
    result = await db.execute(
        select(SpectralDisplayMode).where(SpectralDisplayMode.id == mode_id)
    )
    return result.scalar_one_or_none()


async def create_spectral_mode(
    db: AsyncSession,
    mode_in: SpectralModeCreate,
    *,
    created_by: int | None = None,
) -> SpectralDisplayMode:
    """创建模式."""
    algorithm = await get_display_algorithm_by_code(db, mode_in.gain_algorithm)
    mode = SpectralDisplayMode(
        name=mode_in.name,
        r_channel=mode_in.r_channel,
        g_channel=mode_in.g_channel,
        b_channel=mode_in.b_channel,
        r_gain=mode_in.r_gain,
        g_gain=mode_in.g_gain,
        b_gain=mode_in.b_gain,
        gain_algorithm_id=algorithm.id,
        dark_calibration=mode_in.dark_calibration,
        white_calibration=mode_in.white_calibration,
        created_by=created_by,
    )
    db.add(mode)
    await db.flush()
    await db.refresh(mode)
    return mode


async def update_spectral_mode(
    db: AsyncSession,
    mode: SpectralDisplayMode,
    mode_in: SpectralModeUpdate,
) -> SpectralDisplayMode:
    """更新模式."""
    update_data = mode_in.model_dump(exclude_unset=True)
    if "gain_algorithm" in update_data:
        algorithm = await get_display_algorithm_by_code(db, update_data.pop("gain_algorithm"))
        mode.gain_algorithm_id = algorithm.id
    for field, value in update_data.items():
        setattr(mode, field, value)

    await db.flush()
    await db.refresh(mode)
    return mode


async def delete_spectral_mode(db: AsyncSession, mode: SpectralDisplayMode) -> None:
    """删除模式."""
    await db.delete(mode)
    await db.commit()
