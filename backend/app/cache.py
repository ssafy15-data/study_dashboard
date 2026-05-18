import asyncio
from datetime import UTC, datetime

from app.models import DashboardSnapshot, Member


class DashboardCache:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._snapshot: DashboardSnapshot | None = None
        self._last_error: str | None = None

    async def get_snapshot(self) -> DashboardSnapshot | None:
        async with self._lock:
            return self._snapshot

    async def set_snapshot(self, snapshot: DashboardSnapshot) -> None:
        async with self._lock:
            self._snapshot = snapshot
            self._last_error = None

    async def set_error(self, error: Exception) -> None:
        async with self._lock:
            self._last_error = str(error)

    async def last_refresh(self) -> datetime | None:
        async with self._lock:
            return self._snapshot.last_refresh if self._snapshot else None

    async def last_error(self) -> str | None:
        async with self._lock:
            return self._last_error

    async def ensure_empty_snapshot(self, members: list[str]) -> None:
        async with self._lock:
            if self._snapshot is None:
                self._snapshot = DashboardSnapshot(
                    milestones=[],
                    matrices={},
                    members=[
                        Member(
                            github_id=member,
                            avatar_url=f"https://github.com/{member}.png",
                            total_solved=0,
                            total_possible=0,
                            attendance_rate=0.0,
                        )
                        for member in members
                    ],
                    current_milestone_id=None,
                    last_refresh=datetime.now(UTC),
                )


cache = DashboardCache()
