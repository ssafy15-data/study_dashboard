from datetime import UTC, datetime

from app.data_collector import (
    build_matrix,
    build_milestone_model,
    parse_issue_numbers,
    parse_issue_title,
    select_current_milestone,
)


def test_parse_issue_numbers_from_first_line() -> None:
    assert parse_issue_numbers("Issue: #100, #101\n\nbody") == [100, 101]
    assert parse_issue_numbers("Refs: #100") == []
    assert parse_issue_numbers(None) == []


def test_parse_issue_title() -> None:
    assert parse_issue_title("[LeetCode 3640] Trionic Array II") == (
        "LeetCode",
        "3640",
        "Trionic Array II",
    )
    assert parse_issue_title("No pattern") == ("Unknown", "", "No pattern")


def test_build_matrix_prefers_merged_pr() -> None:
    now = datetime(2026, 5, 17, tzinfo=UTC)
    issues = [
        {
            "number": 116,
            "title": "[SWEA 1855] BFS",
            "html_url": "https://github.com/o/r/issues/116",
            "labels": [{"name": "D5"}],
            "state": "open",
        }
    ]
    milestone = build_milestone_model(
        {
            "id": 5,
            "number": 9,
            "title": "260519 스터디",
            "due_on": "2026-05-19T15:00:00Z",
            "state": "open",
        },
        issues,
        now,
    )
    matrix = build_matrix(
        milestone,
        issues,
        [
            {
                "number": 1,
                "html_url": "https://github.com/o/r/pull/1",
                "body": "Issue: #116",
                "merged_at": None,
                "user": {"login": "dong99u"},
            },
            {
                "number": 2,
                "html_url": "https://github.com/o/r/pull/2",
                "body": "Issue: #116",
                "merged_at": "2026-05-17T00:00:00Z",
                "user": {"login": "dong99u"},
            },
        ],
        ["dong99u", "watermell0n"],
        last_refresh=now,
    )
    assert matrix.matrix["dong99u"]["116"].status == "merged"
    assert matrix.matrix["watermell0n"]["116"].status == "not_submitted"
    assert matrix.summary.total_submissions == 1
    assert matrix.summary.total_possible == 2


def test_select_current_milestone_uses_nearest_open_due() -> None:
    now = datetime(2026, 5, 17, tzinfo=UTC)
    milestones = [
        build_milestone_model(
            {
                "id": 1,
                "number": 1,
                "title": "old",
                "due_on": "2026-05-10T00:00:00Z",
                "state": "open",
            },
            [],
            now,
        ),
        build_milestone_model(
            {
                "id": 2,
                "number": 2,
                "title": "next",
                "due_on": "2026-05-19T00:00:00Z",
                "state": "open",
            },
            [],
            now,
        ),
    ]
    assert select_current_milestone(milestones, now) == 2
