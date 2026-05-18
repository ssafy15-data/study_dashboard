from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.cache import cache
from app.data_collector import build_matrix, build_milestone_model
from app.models import DashboardSnapshot


@pytest.fixture(autouse=True)
async def clear_cache() -> Iterator[None]:
    cache._snapshot = None  # noqa: SLF001
    cache._last_error = None  # noqa: SLF001
    yield
    cache._snapshot = None  # noqa: SLF001
    cache._last_error = None  # noqa: SLF001


@pytest.fixture
def sample_snapshot() -> DashboardSnapshot:
    members = ["alice", "bob"]
    issue = {
        "number": 100,
        "title": "[BOJ 1000] A+B",
        "html_url": "https://github.com/o/r/issues/100",
        "labels": [{"name": "Easy"}],
        "state": "open",
    }
    raw_milestone = {
        "id": 1,
        "number": 5,
        "title": "260519 스터디",
        "due_on": "2026-05-19T15:00:00Z",
        "state": "open",
    }
    milestone = build_milestone_model(raw_milestone, [issue], datetime(2026, 5, 17, tzinfo=UTC))
    matrix = build_matrix(
        milestone,
        [issue],
        [
            {
                "number": 77,
                "html_url": "https://github.com/o/r/pull/77",
                "body": "Issue: #100",
                "merged_at": "2026-05-17T00:00:00Z",
                "user": {"login": "alice"},
            }
        ],
        members,
        last_refresh=datetime(2026, 5, 17, tzinfo=UTC),
    )
    return DashboardSnapshot(
        milestones=[milestone],
        matrices={milestone.id: matrix},
        members=[],
        current_milestone_id=milestone.id,
        last_refresh=datetime(2026, 5, 17, tzinfo=UTC),
    )

