from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from app.models import DashboardSnapshot, MatrixResponse, MatrixSummary, Member, Milestone, Problem

ISSUE_PATTERN = re.compile(r"^\[(\w+)\s+(\d+)\]\s*(.+)$")
PR_ISSUE_PATTERN = re.compile(r"^Issue:\s*(#\d+(?:,\s*#\d+)*)", re.IGNORECASE)


def parse_issue_numbers(body: str | None) -> list[int]:
    if not body:
        return []
    first_line = body.strip().splitlines()[0] if body.strip() else ""
    match = PR_ISSUE_PATTERN.match(first_line)
    if not match:
        return []
    return [int(value.strip().lstrip("#")) for value in match.group(1).split(",")]


def parse_issue_title(title: str) -> tuple[str, str, str]:
    match = ISSUE_PATTERN.match(title)
    if not match:
        return ("Unknown", "", title.strip())
    return (match.group(1), match.group(2), match.group(3).strip())


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _days_left(due_on: datetime | None, now: datetime) -> int | None:
    if not due_on:
        return None
    return (due_on.date() - now.date()).days


def _difficulty(issue: dict[str, Any]) -> str:
    labels = issue.get("labels") or []
    if not labels:
        return ""
    return str(labels[0].get("name", ""))


def build_milestone_model(
    raw: dict[str, Any],
    issues: list[dict[str, Any]],
    now: datetime,
) -> Milestone:
    due_on = _parse_datetime(raw.get("due_on"))
    days_left = _days_left(due_on, now)
    return Milestone(
        id=int(raw["id"]),
        number=int(raw["number"]),
        title=raw["title"],
        due_on=due_on,
        state=raw["state"],
        is_overdue=days_left is not None and days_left < 0,
        days_left=days_left,
        total_issues=len(issues),
        closed_issues=sum(1 for issue in issues if issue.get("state") == "closed"),
    )


def select_current_milestone(milestones: list[Milestone], now: datetime) -> int | None:
    if not milestones:
        return None
    open_with_due = [m for m in milestones if m.state == "open" and m.due_on is not None]
    future_or_today = [m for m in open_with_due if m.due_on and m.due_on >= now]
    if future_or_today:
        return min(future_or_today, key=lambda item: item.due_on or now).id
    if open_with_due:
        return max(open_with_due, key=lambda item: item.due_on or now).id
    open_items = [m for m in milestones if m.state == "open"]
    if open_items:
        return open_items[0].id
    return max(milestones, key=lambda item: item.due_on or datetime.min.replace(tzinfo=UTC)).id


def build_matrix(
    milestone: Milestone,
    issues: list[dict[str, Any]],
    pulls: list[dict[str, Any]],
    members: list[str],
    last_refresh: datetime | None = None,
) -> MatrixResponse:
    issue_numbers = {int(issue["number"]) for issue in issues}
    issue_member_map: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)

    for pr in pulls:
        author = (pr.get("user") or {}).get("login")
        if author not in members:
            continue
        status = "merged" if pr.get("merged_at") else "open_pr"
        for issue_number in parse_issue_numbers(pr.get("body")):
            if issue_number not in issue_numbers:
                continue
            existing = issue_member_map[issue_number].get(author)
            if existing and existing["status"] == "merged":
                continue
            issue_member_map[issue_number][author] = {
                "status": status,
                "pr_number": pr.get("number"),
                "pr_url": pr.get("html_url"),
            }

    problems: list[Problem] = []
    for issue in issues:
        platform, platform_number, name = parse_issue_title(issue["title"])
        problems.append(
            Problem(
                issue_number=int(issue["number"]),
                title=name,
                platform=platform,
                platform_number=platform_number,
                difficulty=_difficulty(issue),
                url=issue["html_url"],
            )
        )

    matrix: dict[str, dict[str, dict[str, Any]]] = {}
    total_submissions = 0
    members_with_missing = 0
    for member in members:
        member_cells: dict[str, dict[str, Any]] = {}
        missing = False
        for issue in issues:
            issue_number = int(issue["number"])
            cell = issue_member_map.get(issue_number, {}).get(member, {"status": "not_submitted"})
            if cell["status"] == "merged":
                total_submissions += 1
            if cell["status"] == "not_submitted":
                missing = True
            member_cells[str(issue_number)] = cell
        matrix[member] = member_cells
        if missing and issues:
            members_with_missing += 1

    total_possible = len(members) * len(issues)
    summary = MatrixSummary(
        total_submissions=total_submissions,
        total_possible=total_possible,
        submission_rate=round(total_submissions / total_possible, 3) if total_possible else 0.0,
        missing_members=members_with_missing,
        total_members=len(members),
    )
    return MatrixResponse(
        milestone=milestone,
        problems=problems,
        members=members,
        matrix=matrix,
        summary=summary,
        last_refresh=last_refresh,
    )


def build_members(matrices: dict[int, MatrixResponse], members: list[str]) -> list[Member]:
    result: list[Member] = []
    for member in members:
        solved = 0
        possible = 0
        for matrix in matrices.values():
            possible += len(matrix.problems)
            solved += sum(
                1 for cell in matrix.matrix.get(member, {}).values() if cell.status == "merged"
            )
        result.append(
            Member(
                github_id=member,
                avatar_url=f"https://github.com/{member}.png",
                total_solved=solved,
                total_possible=possible,
                attendance_rate=round(solved / possible, 3) if possible else 0.0,
            )
        )
    return result


async def collect_dashboard(client: Any, members: list[str]) -> DashboardSnapshot:
    now = datetime.now(UTC)
    raw_milestones = await client.get_milestones(state="all")
    pulls = await client.get_pulls(state="all")

    milestones: list[Milestone] = []
    matrices: dict[int, MatrixResponse] = {}
    for raw_milestone in raw_milestones:
        issues = await client.get_issues(milestone=int(raw_milestone["number"]), state="all")
        milestone = build_milestone_model(raw_milestone, issues, now)
        milestones.append(milestone)
        matrices[milestone.id] = build_matrix(milestone, issues, pulls, members, last_refresh=now)

    milestones.sort(key=lambda item: item.due_on or datetime.min.replace(tzinfo=UTC), reverse=True)
    return DashboardSnapshot(
        milestones=milestones,
        matrices=matrices,
        members=build_members(matrices, members),
        current_milestone_id=select_current_milestone(milestones, now),
        last_refresh=now,
    )
