from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: Literal["ok"]
    last_refresh: datetime | None = None


class Milestone(BaseModel):
    id: int
    number: int
    title: str
    due_on: datetime | None = None
    state: str
    is_overdue: bool
    days_left: int | None = None
    total_issues: int
    closed_issues: int


class Problem(BaseModel):
    issue_number: int
    title: str
    platform: str
    platform_number: str
    difficulty: str
    url: str


class CellStatus(BaseModel):
    status: Literal["merged", "open_pr", "not_submitted"]
    pr_number: int | None = None
    pr_url: str | None = None


class MatrixSummary(BaseModel):
    total_submissions: int
    total_possible: int
    submission_rate: float
    missing_members: int
    total_members: int


class MatrixResponse(BaseModel):
    milestone: Milestone
    problems: list[Problem]
    members: list[str]
    matrix: dict[str, dict[str, CellStatus]]
    summary: MatrixSummary
    last_refresh: datetime | None = None


class Member(BaseModel):
    github_id: str
    avatar_url: str | None = None
    total_solved: int
    total_possible: int
    attendance_rate: float


class DashboardSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    milestones: list[Milestone]
    matrices: dict[int, MatrixResponse]
    members: list[Member]
    current_milestone_id: int | None = None
    last_refresh: datetime | None = None

