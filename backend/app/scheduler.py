from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler(
    refresh_func: Callable[[], Awaitable[None]],
    interval_minutes: int,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_func,
        "interval",
        minutes=interval_minutes,
        id="github-data-refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
