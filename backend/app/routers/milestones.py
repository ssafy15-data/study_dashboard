from fastapi import APIRouter, HTTPException

from app.cache import cache
from app.models import Milestone

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("", response_model=list[Milestone])
async def list_milestones() -> list[Milestone]:
    snapshot = await cache.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="Dashboard data is not loaded yet")
    return snapshot.milestones


@router.get("/current", response_model=Milestone | None)
async def current_milestone() -> Milestone | None:
    snapshot = await cache.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="Dashboard data is not loaded yet")
    if snapshot.current_milestone_id is None:
        return None
    return next(
        (item for item in snapshot.milestones if item.id == snapshot.current_milestone_id),
        None,
    )

