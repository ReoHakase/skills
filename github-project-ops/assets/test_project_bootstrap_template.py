from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ASSET_PATH = Path(__file__).with_name("project-bootstrap-template.py")
FIELDS_PATH = Path(__file__).with_name("project-fields.json")


def load_asset() -> ModuleType:
    spec = importlib.util.spec_from_file_location("project_bootstrap_template", ASSET_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_project_fields_are_loaded_from_json() -> None:
    module = load_asset()

    fields = module.load_project_fields(FIELDS_PATH)

    assert "PROJECT_FIELDS" not in vars(module)
    assert any(field["name"] == "Status" for field in fields)
    assert any(field["name"] == "Scope" and field["type"] == "TEXT" for field in fields)


def test_single_select_options_keep_name_color_and_description() -> None:
    module = load_asset()
    fields = module.load_project_fields(FIELDS_PATH)
    status = next(field for field in fields if field["name"] == "Status")

    assert module.option_names(status["options"]) == [
        "inbox",
        "triaged",
        "ready",
        "in-progress",
        "in-review",
        "blocked",
        "done",
        "canceled",
    ]
    assert (
        module.option_description(status["options"][0])
        == "新しく起票され、まだトリアージされていない。"
    )
    literals = module.single_select_option_literals(status["options"][:1])
    assert 'name:"inbox"' in literals
    assert "color:GRAY" in literals
    assert "description:" in literals


def test_empty_issue_body_stops_before_issue_creation() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="Issue本文が未設定です"):
        module.ensure_issue_bodies({"empty": module.ISSUES[0]})


def test_default_milestone_requires_due_date() -> None:
    module = load_asset()

    assert len(module.MILESTONES) == 1
    assert module.MILESTONES[0].title == "First Release"
    assert module.MILESTONES[0].required_due_on is True
    assert module.MILESTONES[0].due_on == ""


def test_required_milestone_due_date_prompts_when_empty() -> None:
    module = load_asset()
    milestone = module.Milestone(title="First Release", required_due_on=True)

    milestones = module.ensure_milestone_plan([milestone], input_func=lambda _prompt: "2026-07-31")

    assert milestones["First Release"].due_on == "2026-07-31"


def test_invalid_milestone_due_date_is_rejected() -> None:
    module = load_asset()
    milestone = module.Milestone(title="First Release", due_on="2026/07/31")

    with pytest.raises(SystemExit, match="YYYY-MM-DD"):
        module.ensure_milestone_plan([milestone])


def test_unscheduled_milestone_allows_empty_due_date() -> None:
    module = load_asset()
    milestone = module.Milestone(title="法人設立", required_due_on=False)

    milestones = module.ensure_milestone_plan([milestone])

    assert milestones["法人設立"].due_on == ""


def test_duplicate_milestone_titles_are_rejected() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="Milestone titleが重複"):
        module.ensure_milestone_plan(
            [
                module.Milestone(title="First Release", due_on="2026-07-31"),
                module.Milestone(title="First Release", due_on="2026-08-31"),
            ]
        )


def test_default_issue_plan_has_non_overlapping_serial_forecasts() -> None:
    module = load_asset()

    milestones = module.ensure_milestone_plan(
        [module.Milestone(title="First Release", due_on="2026-07-31")]
    )

    module.ensure_issue_plan({issue.title: issue for issue in module.ISSUES}, milestones)


def test_issue_with_unknown_milestone_is_rejected() -> None:
    module = load_asset()
    issue = module.Issue(
        title="Milestone参照Issue",
        body="body",
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="ready",
        forecast_start="2026-06-20",
        forecast_end="2026-06-21",
        milestone="Missing Milestone",
    )

    with pytest.raises(SystemExit, match="milestone=Missing Milestone"):
        module.ensure_issue_plan({issue.title: issue}, {})


def test_github_milestone_due_on_uses_end_of_day_utc() -> None:
    module = load_asset()

    assert module.github_due_on("2026-07-31") == "2026-07-31T23:59:59Z"


def test_ready_issue_with_blocker_is_rejected() -> None:
    module = load_asset()
    blocker = module.Issue(
        title="前段Issue",
        body="body",
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="ready",
        forecast_start="2026-06-20",
        forecast_end="2026-06-21",
    )
    blocked = module.Issue(
        title="後続Issue",
        body="body",
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="ready",
        forecast_start="2026-06-22",
        forecast_end="2026-06-23",
        blocked_by=["前段Issue"],
    )

    with pytest.raises(SystemExit, match="blocked_byがある初期WBS Issueはready"):
        module.ensure_issue_plan({issue.title: issue for issue in [blocker, blocked]})


def test_serial_forecast_overlap_is_rejected() -> None:
    module = load_asset()
    blocker = module.Issue(
        title="前段Issue",
        body="body",
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="ready",
        forecast_start="2026-06-20",
        forecast_end="2026-06-23",
    )
    blocked = module.Issue(
        title="後続Issue",
        body="body",
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="blocked",
        forecast_start="2026-06-23",
        forecast_end="2026-06-24",
        blocked_by=["前段Issue"],
    )

    with pytest.raises(SystemExit, match="直列依存のForecastが重なっています"):
        module.ensure_issue_plan({issue.title: issue for issue in [blocker, blocked]})
