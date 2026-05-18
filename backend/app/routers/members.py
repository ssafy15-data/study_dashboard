from fastapi import APIRouter, HTTPException

from app.cache import cache
from app.models import Member

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[Member])
async def list_members() -> list[Member]:
    snapshot = await cache.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="Dashboard data is not loaded yet")
    return snapshot.members

