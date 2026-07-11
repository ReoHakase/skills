from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ASSET_PATH = Path(__file__).with_name("project-bootstrap-template.py")
FIELDS_PATH = Path(__file__).with_name("project-fields.json")
BACKLOG_PATH = Path(__file__).with_name("backlog.flat.json")


def load_asset() -> ModuleType:
    spec = importlib.util.spec_from_file_location("project_bootstrap_template", ASSET_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_issue(module: ModuleType, title: str, **overrides: Any) -> Any:
    values = {
        "title": title,
        "body": "body",
        "type": "feat",
        "scope": "core",
        "priority": "p2-high",
        "size": "s1-small",
        "complexity": "c1-simple",
        "risk": "r1-safe",
        "agent_tier": "agent-fast",
        "status": "ready",
        "forecast_start": "2026-06-22",
        "forecast_end": "2026-06-22",
        "effort": 1.0,
        "estimate_confidence": "ec2-high",
    }
    values.update(overrides)
    return module.Issue(**values)


def test_project_fields_are_loaded_from_json() -> None:
    module = load_asset()

    fields = module.load_project_fields(FIELDS_PATH)

    assert "PROJECT_FIELDS" not in vars(module)
    assert any(field["name"] == "Status" for field in fields)
    assert any(field["name"] == "Scope" and field["type"] == "TEXT" for field in fields)


def test_capacity_and_claim_fields_are_canonical() -> None:
    module = load_asset()
    fields = module.load_project_fields(FIELDS_PATH)
    by_name = {field["name"]: field for field in fields}

    assert by_name["Effort"] == {"name": "Effort", "type": "NUMBER"}
    assert module.option_names(by_name["Estimate Confidence"]["options"]) == [
        "ec0-low",
        "ec1-medium",
        "ec2-high",
    ]
    assert set(module.option_names(by_name["Estimate Confidence"]["options"])) == (
        module.ESTIMATE_CONFIDENCE_OPTIONS
    )
    assert by_name["Agent Run"] == {"name": "Agent Run", "type": "TEXT"}


def test_backlog_examples_include_estimates_and_empty_agent_run() -> None:
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))

    epic, *leaves = backlog
    assert epic["type"] == "epic"
    assert epic["effort"] is None
    assert epic["estimate_confidence"] == ""
    assert all(issue["effort"] > 0 for issue in leaves)
    assert all(issue["estimate_confidence"].startswith("ec") for issue in leaves)
    assert all(issue["agent_run"] == "" for issue in backlog)


def test_backlog_examples_form_a_three_wave_fork_join() -> None:
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
    by_title = {issue["title"]: issue for issue in backlog}
    contract = "検索レスポンスのデータ契約を定義する"
    ui = "検索結果カードに一致シーンの情報を表示する"
    api = "検索APIから一致シーンを返す"
    integration = "検索結果のend-to-end動作を確認する"

    assert by_title[ui]["blocked_by_titles"] == [contract]
    assert by_title[api]["blocked_by_titles"] == [contract]
    assert set(by_title[integration]["blocked_by_titles"]) == {ui, api}


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
        agent_tier="agent-fast",
        status="ready",
        forecast_start="2026-06-22",
        forecast_end="2026-06-23",
        effort=1.0,
        estimate_confidence="ec2-high",
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
        agent_tier="agent-fast",
        status="ready",
        forecast_start="2026-06-22",
        forecast_end="2026-06-22",
        effort=1.0,
        estimate_confidence="ec2-high",
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
        agent_tier="agent-fast",
        status="ready",
        forecast_start="2026-06-23",
        forecast_end="2026-06-24",
        effort=1.0,
        estimate_confidence="ec2-high",
        blocked_by=["前段Issue"],
    )

    with pytest.raises(SystemExit, match="未解決のblocked_byがある初期WBS Issueはready"):
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
        agent_tier="agent-fast",
        status="ready",
        forecast_start="2026-06-22",
        forecast_end="2026-06-25",
        effort=1.0,
        estimate_confidence="ec2-high",
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
        agent_tier="agent-fast",
        status="blocked",
        forecast_start="2026-06-25",
        forecast_end="2026-06-26",
        effort=1.0,
        estimate_confidence="ec2-high",
        blocked_by=["前段Issue"],
    )

    with pytest.raises(SystemExit, match="直列依存のForecastが重なっています"):
        module.ensure_issue_plan({issue.title: issue for issue in [blocker, blocked]})


def test_number_field_value_is_an_unquoted_graphql_literal() -> None:
    module = load_asset()

    assert module.value_literal("number", 2.5, "Effort", {}) == "{number:2.5}"


def test_forecast_boundaries_must_be_working_days() -> None:
    module = load_asset()
    issue = make_issue(
        module,
        "weekend",
        forecast_start="2026-06-21",
        forecast_end="2026-06-22",
    )

    with pytest.raises(SystemExit, match="Forecast Start は稼働日にしてください"):
        module.ensure_issue_plan({issue.title: issue})


def test_forecast_boundaries_reject_configured_holidays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_asset()
    monkeypatch.setattr(module, "HOLIDAYS", {"2026-06-22"})
    issue = make_issue(module, "holiday")

    with pytest.raises(SystemExit, match="Forecast Start は稼働日にしてください"):
        module.ensure_issue_plan({issue.title: issue})


@pytest.mark.parametrize("value", [True, 0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_effort_values_are_rejected(value: object) -> None:
    module = load_asset()
    issue = make_issue(module, "invalid effort", effort=value)

    with pytest.raises(SystemExit, match="Effortは正の有限数"):
        module.ensure_issue_plan({issue.title: issue})


@pytest.mark.parametrize("issue_type", ["feat", "spike", "docs"])
def test_every_non_epic_type_requires_effort_and_confidence(issue_type: str) -> None:
    module = load_asset()
    missing_effort = make_issue(
        module,
        f"{issue_type} effort",
        type=issue_type,
        effort=None,
        estimate_confidence="ec2-high",
    )
    missing_confidence = make_issue(
        module,
        f"{issue_type} confidence",
        type=issue_type,
        effort=1.0,
        estimate_confidence="",
    )

    with pytest.raises(SystemExit, match="Effortは必須"):
        module.ensure_issue_plan({missing_effort.title: missing_effort})
    with pytest.raises(SystemExit, match="Estimate Confidenceは必須"):
        module.ensure_issue_plan({missing_confidence.title: missing_confidence})


def test_epic_estimate_fields_must_stay_empty() -> None:
    module = load_asset()
    epic = make_issue(
        module,
        "epic",
        type="epic",
        status="triaged",
        agent_tier="",
        effort=None,
        estimate_confidence="",
    )

    module.ensure_issue_plan({epic.title: epic})

    epic.effort = 1.0
    with pytest.raises(SystemExit, match="epicのEffort、Estimate Confidence、Agent Tierは空欄"):
        module.ensure_issue_plan({epic.title: epic})


def test_initial_agent_run_must_stay_empty() -> None:
    module = load_asset()
    issue = make_issue(module, "claimed too early", agent_run="run-123")

    with pytest.raises(SystemExit, match="初期Agent Runは空欄"):
        module.ensure_issue_plan({issue.title: issue})


def test_dependency_self_loop_is_rejected() -> None:
    module = load_asset()
    issue = make_issue(module, "self", status="blocked", blocked_by=["self"])

    with pytest.raises(SystemExit, match="blocked_byの自己参照"):
        module.ensure_issue_plan({issue.title: issue})


def test_duplicate_dependency_is_rejected() -> None:
    module = load_asset()
    blocker = make_issue(module, "blocker")
    issue = make_issue(
        module,
        "duplicate",
        status="blocked",
        blocked_by=["blocker", "blocker"],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )

    with pytest.raises(SystemExit, match="blocked_byが重複"):
        module.ensure_issue_plan({item.title: item for item in [blocker, issue]})


def test_canceled_blocker_does_not_satisfy_dependency() -> None:
    module = load_asset()
    blocker = make_issue(module, "canceled blocker", status="canceled")
    downstream = make_issue(
        module,
        "downstream",
        status="blocked",
        blocked_by=[blocker.title],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )

    with pytest.raises(SystemExit, match="canceled blockerは完了扱いにしません"):
        module.ensure_issue_plan({item.title: item for item in [blocker, downstream]})


def test_done_blocker_allows_ready_dependency() -> None:
    module = load_asset()
    blocker = make_issue(module, "done blocker", status="done")
    downstream = make_issue(
        module,
        "ready downstream",
        status="ready",
        blocked_by=[blocker.title],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )

    module.ensure_issue_plan({item.title: item for item in [blocker, downstream]})


def test_reused_done_blocker_requires_closed_issue_and_done_project_status() -> None:
    module = load_asset()
    blocker = make_issue(module, "done blocker", status="done", number=10)
    downstream = make_issue(
        module,
        "ready downstream",
        status="ready",
        blocked_by=[blocker.title],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )
    issues = {item.title: item for item in [blocker, downstream]}
    existing = [
        {
            "number": 10,
            "title": blocker.title,
            "url": "https://github.com/octo/repo/issues/10",
            "id": "I_10",
            "state": "CLOSED",
        }
    ]
    project_items = {
        "totalCount": 1,
        "items": [
            {
                "id": "PVTI_10",
                "status": "done",
                "content": {"url": "https://github.com/octo/repo/issues/10"},
            }
        ],
    }

    module.validate_reused_done_blockers(issues, existing, project_items)

    project_items["items"][0]["status"] = "in-review"
    with pytest.raises(SystemExit, match="Issue closeとProject Statusを確認できません"):
        module.validate_reused_done_blockers(issues, existing, project_items)


@pytest.mark.parametrize(
    ("size", "complexity", "risk", "expected"),
    [
        ("s1-small", "c1-simple", "r1-safe", "agent-fast"),
        ("s2-medium", "c1-simple", "r1-safe", "agent-standard"),
        ("s1-small", "c3-complex", "r1-safe", "agent-frontier"),
        ("s1-small", "c1-simple", "r3-dangerous", "agent-frontier"),
    ],
)
def test_agent_tier_precedence_is_deterministic(
    size: str, complexity: str, risk: str, expected: str
) -> None:
    module = load_asset()
    issue = make_issue(
        module,
        "tier",
        size=size,
        complexity=complexity,
        risk=risk,
        agent_tier=expected,
        reviewer_owner="reviewer" if risk == "r3-dangerous" else "",
    )

    module.ensure_issue_plan({issue.title: issue})


def test_agent_tier_override_is_rejected() -> None:
    module = load_asset()
    issue = make_issue(module, "wrong tier", agent_tier="agent-standard")

    with pytest.raises(SystemExit, match="Agent Tierが判定式と一致しません"):
        module.ensure_issue_plan({issue.title: issue})


def test_r3_requires_reviewer_owner() -> None:
    module = load_asset()
    issue = make_issue(
        module,
        "dangerous",
        risk="r3-dangerous",
        agent_tier="agent-frontier",
    )

    with pytest.raises(SystemExit, match="Reviewer Owner必須"):
        module.ensure_issue_plan({issue.title: issue})


def test_s3_is_not_ready_without_prior_split_or_exception() -> None:
    module = load_asset()
    issue = make_issue(
        module,
        "large",
        size="s3-large",
        agent_tier="agent-frontier",
    )

    with pytest.raises(SystemExit, match="s3-largeは分割または例外承認前にreadyにしません"):
        module.ensure_issue_plan({issue.title: issue})


def test_dependency_cycle_is_rejected() -> None:
    module = load_asset()
    first = make_issue(module, "first", status="blocked", blocked_by=["third"])
    second = make_issue(module, "second", status="blocked", blocked_by=["first"])
    third = make_issue(module, "third", status="blocked", blocked_by=["second"])

    with pytest.raises(SystemExit, match="blocked_byの循環"):
        module.ensure_issue_plan({item.title: item for item in [first, second, third]})


def test_parent_cycle_is_rejected() -> None:
    module = load_asset()
    first = make_issue(module, "first", parent="third")
    second = make_issue(module, "second", parent="first")
    third = make_issue(module, "third", parent="second")

    with pytest.raises(SystemExit, match="parentの循環"):
        module.ensure_issue_plan({item.title: item for item in [first, second, third]})


def test_three_stage_dependency_chain_is_valid() -> None:
    module = load_asset()
    first = make_issue(module, "first")
    second = make_issue(
        module,
        "second",
        status="blocked",
        blocked_by=["first"],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )
    third = make_issue(
        module,
        "third",
        status="blocked",
        blocked_by=["second"],
        forecast_start="2026-06-24",
        forecast_end="2026-06-24",
    )

    module.ensure_issue_plan({item.title: item for item in [first, second, third]})


def test_fork_join_dependency_graph_is_valid() -> None:
    module = load_asset()
    root = make_issue(module, "root")
    left = make_issue(
        module,
        "left",
        status="blocked",
        blocked_by=["root"],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )
    right = make_issue(
        module,
        "right",
        status="blocked",
        blocked_by=["root"],
        forecast_start="2026-06-23",
        forecast_end="2026-06-23",
    )
    join = make_issue(
        module,
        "join",
        status="blocked",
        blocked_by=["left", "right"],
        forecast_start="2026-06-24",
        forecast_end="2026-06-24",
    )

    module.ensure_issue_plan({item.title: item for item in [root, left, right, join]})


def test_existing_option_ids_are_preserved() -> None:
    module = load_asset()

    materialized = module.materialize_single_select_options(
        [{"name": "ready", "color": "GREEN", "description": "開始可能"}],
        [{"id": "OPT_ready", "name": "ready", "color": "BLUE", "description": "旧"}],
    )

    assert materialized == [
        {
            "id": "OPT_ready",
            "name": "ready",
            "color": "GREEN",
            "description": "開始可能",
        }
    ]
    assert 'id:"OPT_ready"' in module.single_select_option_literals(materialized)


def test_unchanged_options_skip_update() -> None:
    module = load_asset()
    current = [{"id": "OPT_ready", "name": "ready", "color": "GREEN", "description": "開始可能"}]

    materialized = module.materialize_single_select_options(current, current)

    assert module.option_signatures(materialized) == module.option_signatures(current)


def test_option_removal_or_rename_is_rejected() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="削除・rename"):
        module.materialize_single_select_options(
            [{"name": "renamed", "color": "GREEN"}],
            [{"id": "OPT_ready", "name": "ready", "color": "GREEN"}],
        )


def test_option_replacement_is_allowed_only_for_proven_empty_project() -> None:
    module = load_asset()

    materialized = module.materialize_single_select_options(
        [{"name": "ready", "color": "GREEN"}],
        [{"id": "OPT_todo", "name": "Todo", "color": "GRAY"}],
        allow_removal=True,
    )

    assert materialized == [{"id": "", "name": "ready", "color": "GREEN", "description": ""}]


def test_string_option_preserves_existing_metadata() -> None:
    module = load_asset()

    materialized = module.materialize_single_select_options(
        ["ready"],
        [
            {
                "id": "OPT_ready",
                "name": "ready",
                "color": "PURPLE",
                "description": "既存説明",
            }
        ],
    )

    assert materialized[0]["color"] == "PURPLE"
    assert materialized[0]["description"] == "既存説明"


def test_duplicate_option_names_are_rejected() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="option名が重複"):
        module.materialize_single_select_options(["ready", "ready"], [])


def test_existing_field_data_type_must_match(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_asset()
    monkeypatch.setattr(
        module,
        "list_project_fields",
        lambda: {"Status": {"id": "FIELD", "name": "Status", "dataType": "TEXT"}},
    )

    with pytest.raises(SystemExit, match="既存fieldの型が一致しません"):
        module.ensure_project_fields(
            [{"name": "Status", "type": "SINGLE_SELECT", "options": ["ready"]}]
        )


def test_graphql_payload_errors_fail_even_with_success_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_asset()
    payload = {"data": {}, "errors": [{"message": "Resource not accessible"}]}
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )

    with pytest.raises(SystemExit):
        module.graphql_json("query { viewer { login } }")


def test_mixed_duplicate_and_permission_errors_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_asset()
    payload = {
        "data": {},
        "errors": [
            {"message": "Issue is already blocked by this issue"},
            {"message": "Resource not accessible by integration"},
        ],
    }
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=1, stdout=json.dumps(payload), stderr=""
        ),
    )

    with pytest.raises(SystemExit):
        module.graphql_json("mutation { noop }", duplicate_operation="blocked-by")


def test_expected_duplicate_relation_error_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_asset()
    payload = {
        "data": {"addBlockedBy": None},
        "errors": [{"message": "Issue is already blocked by this issue"}],
    }
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=1, stdout=json.dumps(payload), stderr=""
        ),
    )

    assert module.graphql_json("mutation { noop }", duplicate_operation="blocked-by") == payload


def test_template_placeholders_fail_before_gh_call(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_asset()
    monkeypatch.setattr(module, "REPO", "OWNER/REPO")

    with pytest.raises(SystemExit, match="REPOを確認済み"):
        module.validate_configuration()


def test_unlinked_repository_fails_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_asset()
    monkeypatch.setattr(module, "OWNER", "@me")
    monkeypatch.setattr(module, "REPO", "octo/repo")
    monkeypatch.setattr(module, "PROJECT_NUMBER", "7")
    monkeypatch.setattr(module, "PROJECT_ID", "PVT_target")
    monkeypatch.setattr(
        module,
        "graphql_json",
        lambda *_args, **_kwargs: {
            "data": {
                "viewer": {"login": "octo"},
                "repository": {
                    "id": "R_repo",
                    "nameWithOwner": "octo/repo",
                    "defaultBranchRef": {"name": "trunk"},
                    "projectsV2": {
                        "nodes": [{"id": "PVT_other", "number": 8}],
                        "pageInfo": {"hasNextPage": False},
                    },
                },
                "node": {
                    "id": "PVT_target",
                    "number": 7,
                    "owner": {"login": "octo"},
                    "url": "https://github.com/users/octo/projects/7",
                    "items": {"totalCount": 0},
                },
            }
        },
    )

    with pytest.raises(SystemExit, match="linkされていません"):
        module.discover_target()


def test_issue_reuse_requires_explicit_number() -> None:
    module = load_asset()
    issue = module.ISSUES[0]
    existing = [
        {
            "number": 42,
            "title": issue.title,
            "url": "https://github.com/octo/repo/issues/42",
            "id": "I_42",
        }
    ]

    with pytest.raises(SystemExit, match="Issue.numberを明示"):
        module.validate_issue_reuse({issue.title: issue}, existing)


def test_duplicate_issue_titles_are_rejected() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="Issue titleが重複"):
        module.index_issues([module.ISSUES[0], module.ISSUES[0]])


def test_project_item_fallback_matches_url_not_title() -> None:
    module = load_asset()
    data = {
        "totalCount": 2,
        "items": [
            {
                "id": "PVTI_expected",
                "content": {
                    "title": "同名Issue",
                    "url": "https://github.com/octo/repo/issues/10",
                },
            },
            {
                "id": "PVTI_other",
                "content": {
                    "title": "同名Issue",
                    "url": "https://github.com/octo/repo/issues/11",
                },
            },
        ],
    }

    assert module.project_items_by_url(data)["https://github.com/octo/repo/issues/10"] == (
        "PVTI_expected"
    )


def test_incomplete_project_item_page_is_rejected() -> None:
    module = load_asset()

    with pytest.raises(SystemExit, match="全件取得できません"):
        module.project_items_by_url({"totalCount": 2, "items": [{"id": "one"}]})


def test_plan_mode_never_calls_apply(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_asset()
    monkeypatch.setattr(module, "prepare_bootstrap", lambda: {"prepared": True})
    monkeypatch.setattr(
        module,
        "build_bootstrap_plan",
        lambda *_args, **_kwargs: {"mode": "plan", "blockers": []},
    )
    monkeypatch.setattr(
        module,
        "apply_bootstrap",
        lambda *_args, **_kwargs: pytest.fail("planからmutationへ到達した"),
    )

    module.main(["plan"])

    assert '"mode": "plan"' in capsys.readouterr().out


def test_wrong_apply_confirmation_stops_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_asset()
    monkeypatch.setattr(module, "REPO", "octo/repo")
    monkeypatch.setattr(module, "PROJECT_NUMBER", "7")
    monkeypatch.setattr(module, "prepare_bootstrap", lambda: {"prepared": True})
    monkeypatch.setattr(
        module,
        "build_bootstrap_plan",
        lambda *_args, **_kwargs: {"mode": "plan", "blockers": []},
    )
    monkeypatch.setattr(
        module,
        "apply_bootstrap",
        lambda *_args, **_kwargs: pytest.fail("確認前にmutationへ到達した"),
    )

    with pytest.raises(SystemExit, match="確認文字列が一致しません"):
        module.main(["apply", "--confirm", "wrong"])


def test_copyable_ci_placeholder_fails_closed() -> None:
    workflow = ASSET_PATH.parent / ".github" / "workflows" / "ci.yml"
    content = workflow.read_text(encoding="utf-8")

    assert "exit 1" in content
