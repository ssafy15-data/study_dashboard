from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Response, status

from app.cache import cache
from app.models import HealthResponse

router = APIRouter(tags=["system"])
_refresh_handler: Callable[[], Awaitable[None]] | None = None


def set_refresh_handler(handler: Callable[[], Awaitable[None]]) -> None:
    global _refresh_handler
    _refresh_handler = handler


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", last_refresh=await cache.last_refresh())


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(response: Response) -> Response:
    if _refresh_handler is not None:
        await _refresh_handler()
    return response
