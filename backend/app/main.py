from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import cache
from app.config import get_settings
from app.data_collector import collect_dashboard
from app.github_client import GitHubClient
from app.routers import matrix, members, milestones, stats, system
from app.scheduler import create_scheduler

settings = get_settings()


async def refresh_dashboard() -> None:
    try:
        async with GitHubClient(
            owner=settings.github_owner,
            repo=settings.github_repo,
            token=settings.github_token,
        ) as client:
            snapshot = await collect_dashboard(client, settings.members)
            await cache.set_snapshot(snapshot)
    except Exception as exc:
        await cache.set_error(exc)
        await cache.ensure_empty_snapshot(settings.members)
        raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    system.set_refresh_handler(refresh_dashboard)
    try:
        await refresh_dashboard()
    except Exception:
        pass
    scheduler = create_scheduler(refresh_dashboard, settings.refresh_interval_minutes)
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="PS Study Dashboard API", version="0.1.0", lifespan=lifespan)
allow_all_origins = settings.allowed_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api")
app.include_router(milestones.router, prefix="/api")
app.include_router(matrix.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
