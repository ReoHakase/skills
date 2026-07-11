from __future__ import annotations

import importlib.util
import json
import subprocess
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
