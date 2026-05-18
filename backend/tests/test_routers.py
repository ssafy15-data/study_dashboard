from fastapi.testclient import TestClient

from app.cache import cache
from app.main import app


def test_health_returns_last_refresh(sample_snapshot) -> None:
    async def seed() -> None:
        await cache.set_snapshot(sample_snapshot)

    import asyncio

    asyncio.run(seed())
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_current_matrix(sample_snapshot) -> None:
    async def seed() -> None:
        await cache.set_snapshot(sample_snapshot)

    import asyncio

    asyncio.run(seed())
    client = TestClient(app)
    response = client.get("/api/matrix")
    assert response.status_code == 200
    assert response.json()["summary"]["total_submissions"] == 1
