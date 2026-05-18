import asyncio
from collections.abc import AsyncIterator
from email.utils import parsedate_to_datetime

import httpx


class GitHubClientError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, owner: str, repo: str, token: str = "") -> None:
        self.owner = owner
        self.repo = repo
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ps-study-dashboard",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers,
            timeout=httpx.Timeout(20.0),
        )

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, path: str, params: dict[str, object] | None = None) -> httpx.Response:
        response = await self._client.get(path, params=params)
        if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
            reset_at = response.headers.get("x-ratelimit-reset")
            raise GitHubClientError(f"GitHub API rate limit exceeded; reset epoch={reset_at}")
        if response.status_code in {502, 503, 504}:
            await asyncio.sleep(1)
            response = await self._client.get(path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            retry_after = response.headers.get("retry-after")
            reset = response.headers.get("x-ratelimit-reset")
            date = (
                parsedate_to_datetime(response.headers["date"])
                if "date" in response.headers
                else None
            )
            raise GitHubClientError(
                f"GitHub request failed: {response.status_code} {path}; "
                f"retry_after={retry_after}; reset={reset}; date={date}"
            ) from exc
        return response

    async def _paginate(
        self, path: str, params: dict[str, object] | None = None
    ) -> AsyncIterator[dict]:
        page = 1
        base_params = dict(params or {})
        while True:
            response = await self._request(path, {**base_params, "per_page": 100, "page": page})
            items = response.json()
            if not items:
                break
            for item in items:
                yield item
            if 'rel="next"' not in response.headers.get("link", ""):
                break
            page += 1

    async def get_milestones(self, state: str = "all") -> list[dict]:
        path = f"/repos/{self.owner}/{self.repo}/milestones"
        return [item async for item in self._paginate(path, {"state": state, "sort": "due_on"})]

    async def get_issues(self, milestone: int | str, state: str = "all") -> list[dict]:
        path = f"/repos/{self.owner}/{self.repo}/issues"
        params = {"state": state, "milestone": milestone, "sort": "created", "direction": "asc"}
        items = [item async for item in self._paginate(path, params)]
        return [item for item in items if "pull_request" not in item]

    async def get_pulls(self, state: str = "all") -> list[dict]:
        path = f"/repos/{self.owner}/{self.repo}/pulls"
        return [item async for item in self._paginate(path, {"state": state, "sort": "updated"})]

    async def get_user(self, login: str) -> dict | None:
        response = await self._request(f"/users/{login}")
        return response.json()
