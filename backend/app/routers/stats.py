from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def stats_placeholder() -> dict[str, str]:
    return {"status": "planned", "phase": "2"}

