"""github-project-ops用の編集可能なGitHub Project bootstrapテンプレート。

これはそのまま使う丸ごと実行用スクリプトではない。一時パスへコピーし、設定欄を
確認済みのGitHub値へ置き換え、ISSUESを見直してから実行する。

必要なツール:
- リポジトリとprojectスコープで認証済みのgh CLI
- Python 3.10+
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from textwrap import dedent
from typing import Any, Literal

# 実行前にこの設定欄を置き換える。
OWNER = "@me"
REPO = "OWNER/REPO"
PROJECT_NUMBER = "1"
PROJECT_ID = "PVT_REPLACE_ME"
# テンプレートだけを一時パスへコピーする場合は、project-fields.jsonも同じディレクトリへ置くか、
# この値を絶対パスへ置き換える。
PROJECT_FIELDS_PATH = Path(__file__).resolve().with_name("project-fields.json")


OPTION_COLORS = ["GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE"]
VALID_OPTION_COLORS = set(OPTION_COLORS)
OptionSpec = str | dict[str, str]
FieldKind = Literal["single", "text", "date"]

PLACEHOLDER_VALUES = {"OWNER/REPO", "PVT_REPLACE_ME"}
EXPECTED_DUPLICATE_MARKERS = {
    "sub-issue": (
        "already a sub-issue",
        "already has this parent",
    ),
    "blocked-by": (
        "already blocked by",
        "blocking relationship already exists",
    ),
    "project-item": (
        "already exists in this project",
        "already added to this project",
    ),
}


@dataclass
class Milestone:
    title: str
    description: str = ""
    due_on: str = ""
    required_due_on: bool = False
    number: int | None = None


@dataclass
class Issue:
    title: str
    body: str
    type: str
    scope: str
    priority: str
    size: str
    complexity: str
    risk: str
    agent_tier: str
    status: str
    forecast_start: str
    forecast_end: str
    source: str = "docs"
    reviewer_owner: str = ""
    milestone: str = ""
    parent: str | None = None
    blocked_by: list[str] = field(default_factory=list)
    number: int | None = None
    url: str | None = None
    node_id: str | None = None
    item_id: str | None = None


MILESTONES: list[Milestone] = [
    Milestone(
        title="First Release",
        description="初回利用可能版。Milestone期限を先に決めてからIssue/WBSのForecastを組む。",
        required_due_on=True,
    )
]


# Issue本文の構成と記入例は ../references/issue-authoring.md を参照する。
# 対象リポジトリ用の本文だけを body=dedent("""...""").strip() へ入れる。
ISSUES: list[Issue] = [
    Issue(
        title="親Issueの例",
        body=dedent(""" """).strip(),
        type="epic",
        scope="core",
        priority="p2-high",
        size="s0-tiny",
        complexity="c1-simple",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="triaged",
        forecast_start="2026-06-20",
        forecast_end="2026-06-27",
        milestone="First Release",
    ),
    Issue(
        title="子Issueの例",
        body=dedent(""" """).strip(),
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c2-moderate",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="ready",
        forecast_start="2026-06-20",
        forecast_end="2026-06-23",
        milestone="First Release",
        parent="親Issueの例",
    ),
    Issue(
        title="直列の後続子Issueの例",
        body=dedent(""" """).strip(),
        type="feat",
        scope="core",
        priority="p2-high",
        size="s1-small",
        complexity="c2-moderate",
        risk="r1-safe",
        agent_tier="agent-standard",
        status="blocked",
        forecast_start="2026-06-24",
        forecast_end="2026-06-27",
        milestone="First Release",
        parent="親Issueの例",
        blocked_by=["子Issueの例"],
    ),
]


def run_gh(args: list[str], *, input_text: str | None = None, check: bool = True) -> str:
    proc = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if check and proc.returncode != 0:
        print("コマンド失敗:", " ".join(args), file=sys.stderr)
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    if not check and proc.returncode != 0:
        message = (proc.stderr or proc.stdout).strip().splitlines()
        print("警告:", " ".join(args), message[-1] if message else "失敗", file=sys.stderr)
    return proc.stdout


def gh_json(args: list[str], *, input_text: str | None = None) -> Any:
    return json.loads(run_gh(args, input_text=input_text))


def is_expected_duplicate_error(error: dict[str, Any], operation: str) -> bool:
    message = str(error.get("message", "")).lower()
    return any(marker in message for marker in EXPECTED_DUPLICATE_MARKERS[operation])


def graphql_json(
    query: str,
    variables: dict[str, str] | None = None,
    *,
    duplicate_operation: str | None = None,
) -> dict[str, Any]:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for name, value in (variables or {}).items():
        args.extend(["-F", f"{name}={value}"])

    proc = subprocess.run(args, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    errors = payload.get("errors", []) if isinstance(payload, dict) else []

    if errors:
        if duplicate_operation and all(
            is_expected_duplicate_error(error, duplicate_operation) for error in errors
        ):
            print(
                f"警告: 既存の{duplicate_operation}関係を再利用します",
                file=sys.stderr,
            )
            return payload
        print(json.dumps(errors, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(proc.returncode or 1)

    if proc.returncode != 0:
        print("コマンド失敗:", " ".join(args), file=sys.stderr)
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)

    if not isinstance(payload, dict):
        raise SystemExit("GraphQL responseがobjectではありません")
    return payload


def load_project_fields(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Project field定義が見つかりません: {path}。"
            "project-fields.jsonをテンプレートと同じディレクトリへ置くか、"
            "PROJECT_FIELDS_PATHを設定してください。"
        ) from exc

    if not isinstance(data, list):
        raise SystemExit(f"Project field定義はlistである必要があります: {path}")
    return data


def gql_string(value: str) -> str:
    return json.dumps(value)


def option_name(option_spec: OptionSpec) -> str:
    if isinstance(option_spec, str):
        return option_spec
    name = option_spec.get("name")
    if not name:
        raise ValueError(f"単一選択の選択肢にnameがありません: {option_spec}")
    return name


def option_color(option_spec: OptionSpec, idx: int) -> str:
    color = option_spec.get("color") if isinstance(option_spec, dict) else ""
    color = (color or OPTION_COLORS[idx % len(OPTION_COLORS)]).upper()
    if color not in VALID_OPTION_COLORS:
        raise ValueError(f"未対応のGitHub Project選択肢の色: {color}")
    return color


def option_description(option_spec: OptionSpec) -> str:
    if isinstance(option_spec, str):
        return ""
    return str(option_spec.get("description") or "")


def option_id(option_spec: OptionSpec) -> str:
    if isinstance(option_spec, str):
        return ""
    return str(option_spec.get("id") or "")


def has_option_metadata(options: Sequence[OptionSpec]) -> bool:
    return any(
        isinstance(option_spec, dict) and ("color" in option_spec or "description" in option_spec)
        for option_spec in options
    )


def option_names(options: Sequence[OptionSpec]) -> list[str]:
    return [option_name(option_spec) for option_spec in options]


def list_project_fields() -> dict[str, dict[str, Any]]:
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 100) {
            nodes {
              __typename
              ... on ProjectV2Field { id name dataType }
              ... on ProjectV2SingleSelectField {
                id name dataType
                options { id name color description }
              }
              ... on ProjectV2IterationField { id name dataType }
            }
            pageInfo { hasNextPage }
          }
        }
      }
    }
    """
    payload = graphql_json(query, {"projectId": PROJECT_ID})
    connection = payload.get("data", {}).get("node", {}).get("fields", {})
    if connection.get("pageInfo", {}).get("hasNextPage"):
        raise SystemExit("Project fieldが100件を超えています。pagination対応後に実行してください。")
    return {
        field_data["name"]: field_data
        for field_data in connection.get("nodes", [])
        if field_data.get("name") and field_data.get("dataType")
    }


def single_select_option_literals(options: Sequence[OptionSpec]) -> str:
    option_literals = []
    for idx, option_spec in enumerate(options):
        existing_id = option_id(option_spec)
        id_literal = f"id:{gql_string(existing_id)}," if existing_id else ""
        option_literals.append(
            f"{{{id_literal}name:{gql_string(option_name(option_spec))},"
            f"color:{option_color(option_spec, idx)},"
            f"description:{gql_string(option_description(option_spec))}}}"
        )
    return ",".join(option_literals)


def materialize_single_select_options(
    desired_options: Sequence[OptionSpec],
    current_options: list[dict[str, Any]],
    *,
    allow_removal: bool = False,
) -> list[dict[str, str]]:
    desired_names = option_names(desired_options)
    current_names = [str(option.get("name", "")) for option in current_options]
    if len(desired_names) != len(set(desired_names)):
        raise SystemExit(f"single-select option名が重複しています: {desired_names}")
    if len(current_names) != len(set(current_names)):
        raise SystemExit(f"既存single-select option名が重複しています: {current_names}")

    current_by_name = {option["name"]: option for option in current_options}
    removed_names = sorted(set(current_by_name) - set(desired_names))
    if removed_names and not allow_removal:
        raise SystemExit(
            "既存single-select optionの削除・renameはbootstrapで行いません: "
            f"{removed_names}。値をexportした専用migrationを作成してください。"
        )

    preserved: list[dict[str, str]] = []
    for option_spec in desired_options:
        name = option_name(option_spec)
        current = current_by_name.get(name, {})
        current_id = str(current.get("id", ""))
        if current and not current_id:
            raise SystemExit(f"既存single-select optionにIDがありません: {name}")
        if isinstance(option_spec, str):
            color = str(current.get("color") or option_color(option_spec, len(preserved)))
            description = str(current.get("description") or "")
        else:
            color = option_color(option_spec, len(preserved))
            description = option_description(option_spec)
        preserved.append(
            {
                "id": current_id,
                "name": name,
                "color": color,
                "description": description,
            }
        )
    return preserved


def option_signatures(options: Sequence[OptionSpec]) -> list[tuple[str, str, str, str]]:
    return [
        (
            option_id(option),
            option_name(option),
            option_color(option, idx),
            option_description(option),
        )
        for idx, option in enumerate(options)
    ]


def update_single_select_options(field_id: str, options: Sequence[OptionSpec]) -> None:
    mutation = (
        "mutation { "
        f"updateProjectV2Field(input:{{fieldId:{gql_string(field_id)},"
        f"singleSelectOptions:[{single_select_option_literals(options)}]}}) "
        "{ projectV2Field { ... on ProjectV2SingleSelectField { id name options { id name } } } } "
        "}"
    )
    graphql_json(mutation)


def ensure_project_fields(
    project_fields: list[dict[str, Any]],
    *,
    update_existing: bool = False,
    allow_empty_project_option_migration: bool = False,
) -> dict[str, dict[str, Any]]:
    fields = list_project_fields()
    allow_removal = allow_empty_project_option_migration and project_item_count() == 0
    for field_data in project_fields:
        existing = fields.get(field_data["name"])
        options = field_data.get("options", [])
        if existing:
            existing_type = existing.get("dataType")
            if existing_type and existing_type != field_data["type"]:
                raise SystemExit(
                    f"既存fieldの型が一致しません: {field_data['name']} "
                    f"({existing_type} != {field_data['type']})"
                )
            if field_data["type"] == "SINGLE_SELECT":
                current_options = existing.get("options", [])
                materialized = materialize_single_select_options(
                    options, current_options, allow_removal=allow_removal
                )
                needs_update = option_signatures(materialized) != option_signatures(current_options)
                if needs_update and not update_existing:
                    raise SystemExit(
                        f"既存fieldのoption差分があります: {field_data['name']}。"
                        "内容を確認し、明示的な既存field更新として再実行してください。"
                    )
                if needs_update and update_existing:
                    update_single_select_options(existing["id"], materialized)
            continue

        cmd = [
            "gh",
            "project",
            "field-create",
            PROJECT_NUMBER,
            "--owner",
            OWNER,
            "--name",
            field_data["name"],
            "--data-type",
            field_data["type"],
            "--format",
            "json",
        ]
        if field_data["type"] == "SINGLE_SELECT":
            cmd.extend(["--single-select-options", ",".join(option_names(options))])
        gh_json(cmd)
        fields = list_project_fields()
        if field_data["type"] == "SINGLE_SELECT" and has_option_metadata(options):
            created = fields[field_data["name"]]
            materialized = materialize_single_select_options(options, created.get("options", []))
            update_single_select_options(created["id"], materialized)
    return list_project_fields()


def list_issues() -> list[dict[str, Any]]:
    data = gh_json(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,url,id,state",
        ]
    )
    return data


def validate_configuration() -> None:
    if REPO in PLACEHOLDER_VALUES or "/" not in REPO:
        raise SystemExit(f"REPOを確認済みのOWNER/REPOへ置き換えてください: {REPO}")
    if PROJECT_ID in PLACEHOLDER_VALUES or not PROJECT_ID.startswith("PVT_"):
        raise SystemExit(f"PROJECT_IDを確認済みのnode IDへ置き換えてください: {PROJECT_ID}")
    if not PROJECT_NUMBER.isdigit():
        raise SystemExit(f"PROJECT_NUMBERは数字で指定してください: {PROJECT_NUMBER}")
    if not OWNER.strip():
        raise SystemExit("OWNERをProject owner loginまたは@meで指定してください")


def discover_target() -> dict[str, Any]:
    repo_owner, repo_name = REPO.split("/", 1)
    query = """
    query($repoOwner: String!, $repoName: String!, $projectId: ID!) {
      viewer { login }
      repository(owner: $repoOwner, name: $repoName) {
        id nameWithOwner url isPrivate
        defaultBranchRef { name }
        projectsV2(first: 100) {
          nodes { id number }
          pageInfo { hasNextPage }
        }
      }
      node(id: $projectId) {
        ... on ProjectV2 {
          id number title url
          items(first: 1) { totalCount }
          owner {
            ... on Organization { login }
            ... on User { login }
          }
        }
      }
    }
    """
    payload = graphql_json(
        query,
        {"repoOwner": repo_owner, "repoName": repo_name, "projectId": PROJECT_ID},
    )
    data = payload.get("data", {})
    repository = data.get("repository")
    project = data.get("node")
    if not repository or not project:
        raise SystemExit("repositoryまたはProjectを取得できませんでした")
    if repository.get("nameWithOwner") != REPO or not repository.get("defaultBranchRef"):
        raise SystemExit(
            f"repositoryまたはdefault branchが一致しません: {repository.get('nameWithOwner')}"
        )
    expected_owner = data.get("viewer", {}).get("login") if OWNER == "@me" else OWNER.lstrip("@")
    actual_owner = project.get("owner", {}).get("login")
    if actual_owner != expected_owner:
        raise SystemExit(f"Project ownerが一致しません: {actual_owner} != {expected_owner}")
    if str(project.get("number")) != PROJECT_NUMBER or project.get("id") != PROJECT_ID:
        raise SystemExit(
            "Project number / IDが一致しません: "
            f"number={project.get('number')} id={project.get('id')}"
        )
    if not isinstance(project.get("items", {}).get("totalCount"), int):
        raise SystemExit("Project item countを検証できません")
    project_connection = repository.get("projectsV2", {})
    if project_connection.get("pageInfo", {}).get("hasNextPage"):
        raise SystemExit("linked Projectが100件を超え、対象Projectとのlinkを検証できません")
    linked_ids = {item.get("id") for item in project_connection.get("nodes", [])}
    if PROJECT_ID not in linked_ids:
        raise SystemExit(f"Projectがrepositoryへlinkされていません: {REPO} -> {PROJECT_ID}")
    return {"repository": repository, "project": project}


def project_item_count() -> int:
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 { items(first: 1) { totalCount } }
      }
    }
    """
    payload = graphql_json(query, {"projectId": PROJECT_ID})
    count = payload.get("data", {}).get("node", {}).get("items", {}).get("totalCount")
    if not isinstance(count, int):
        raise SystemExit("Project item countを検証できません")
    return count


def validate_issue_reuse(issues: dict[str, Issue], existing: list[dict[str, Any]]) -> None:
    existing_by_number = {int(item["number"]): item for item in existing}
    existing_by_title: dict[str, list[dict[str, Any]]] = {}
    for item in existing:
        existing_by_title.setdefault(item["title"], []).append(item)

    for issue in issues.values():
        if issue.number is not None:
            match = existing_by_number.get(issue.number)
            if not match:
                raise SystemExit(
                    f"再利用するIssueが見つかりません: #{issue.number} ({issue.title})"
                )
            if match["title"] != issue.title:
                raise SystemExit(
                    f"再利用するIssue titleが一致しません: #{issue.number} "
                    f"{match['title']} != {issue.title}"
                )
        elif existing_by_title.get(issue.title):
            urls = [item["url"] for item in existing_by_title[issue.title]]
            raise SystemExit(
                f"同名Issueが既にあります: {issue.title} {urls}。"
                "再利用する場合はIssue.numberを明示してください。"
            )


def hydrate_explicit_issues(issues: dict[str, Issue], existing: list[dict[str, Any]]) -> None:
    existing_by_number = {int(item["number"]): item for item in existing}
    for issue in issues.values():
        if issue.number is None:
            continue
        match = existing_by_number[issue.number]
        issue.url = match["url"]
        issue.node_id = match["id"]


def index_issues(issue_specs: list[Issue]) -> dict[str, Issue]:
    issues: dict[str, Issue] = {}
    duplicates: list[str] = []
    for issue in issue_specs:
        if issue.title in issues:
            duplicates.append(issue.title)
        issues[issue.title] = issue
    if duplicates:
        raise SystemExit(f"Issue titleが重複しています: {sorted(set(duplicates))}")
    return issues


def ensure_issue_bodies(issues: dict[str, Issue]) -> None:
    missing = [issue.title for issue in issues.values() if not issue.body.strip()]
    if missing:
        raise SystemExit(
            "Issue本文が未設定です: "
            f"{missing}。../references/issue-authoring.md を参照して本文を記入してください。"
        )


def parse_iso_date(label: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"{label} はYYYY-MM-DDで指定してください: {value}") from exc


def parse_forecast_date(issue: Issue, field_name: str, value: str) -> date:
    return parse_iso_date(f"{issue.title} の {field_name}", value)


def forecast_range(issue: Issue) -> tuple[date, date]:
    if not issue.forecast_start or not issue.forecast_end:
        raise SystemExit(f"Forecast Start / Forecast Endが未設定です: {issue.title}")
    start = parse_forecast_date(issue, "Forecast Start", issue.forecast_start)
    end = parse_forecast_date(issue, "Forecast End", issue.forecast_end)
    if start > end:
        raise SystemExit(
            f"Forecast StartがForecast Endより後です: "
            f"{issue.title} ({issue.forecast_start} > {issue.forecast_end})"
        )
    return start, end


def prompt_required_milestone_due_on(
    milestone: Milestone, *, input_func: Callable[[str], str] = input
) -> str:
    while True:
        value = input_func(f"{milestone.title} milestone due date (YYYY-MM-DD): ").strip()
        if not value:
            print(f"{milestone.title} の期限は必須です。", file=sys.stderr)
            continue
        parse_iso_date(f"{milestone.title} milestone due date", value)
        return value


def ensure_milestone_plan(
    milestones: list[Milestone], *, input_func: Callable[[str], str] = input
) -> dict[str, Milestone]:
    by_title: dict[str, Milestone] = {}
    duplicates: list[str] = []
    for milestone in milestones:
        if milestone.title in by_title:
            duplicates.append(milestone.title)
        by_title[milestone.title] = milestone

    if duplicates:
        raise SystemExit(f"Milestone titleが重複しています: {duplicates}")

    for milestone in milestones:
        if milestone.required_due_on and not milestone.due_on:
            milestone.due_on = prompt_required_milestone_due_on(milestone, input_func=input_func)
        if milestone.due_on:
            parse_iso_date(f"{milestone.title} milestone due date", milestone.due_on)

    return by_title


def github_due_on(due_on: str) -> str:
    return f"{parse_iso_date('Milestone due date', due_on).isoformat()}T23:59:59Z"


def ensure_issue_plan(
    issues: dict[str, Issue], milestones: dict[str, Milestone] | None = None
) -> None:
    missing_refs: list[str] = []
    for issue in issues.values():
        if issue.parent and issue.parent not in issues:
            missing_refs.append(f"{issue.title} parent={issue.parent}")
        for blocker_title in issue.blocked_by:
            if blocker_title not in issues:
                missing_refs.append(f"{issue.title} blocked_by={blocker_title}")
        if milestones is not None and issue.milestone and issue.milestone not in milestones:
            missing_refs.append(f"{issue.title} milestone={issue.milestone}")
    if missing_refs:
        raise SystemExit(f"Issue relationの参照先が見つかりません: {missing_refs}")

    for issue in issues.values():
        if issue.type == "epic" and issue.status == "ready":
            raise SystemExit(f"epic Issueはreadyにしません: {issue.title}")
        if issue.blocked_by and issue.status == "ready":
            raise SystemExit(f"blocked_byがある初期WBS Issueはreadyにしません: {issue.title}")

    forecasts = {issue.title: forecast_range(issue) for issue in issues.values()}
    for issue in issues.values():
        issue_start, _ = forecasts[issue.title]
        for blocker_title in issue.blocked_by:
            _, blocker_end = forecasts[blocker_title]
            if issue_start <= blocker_end:
                raise SystemExit(
                    "直列依存のForecastが重なっています: "
                    f"{issue.title} starts {issue.forecast_start}, "
                    f"but blocker {blocker_title} ends {issues[blocker_title].forecast_end}"
                )


def list_milestones() -> dict[str, dict[str, Any]]:
    data = gh_json(
        [
            "gh",
            "api",
            f"repos/{REPO}/milestones",
            "--method",
            "GET",
            "-f",
            "state=all",
            "-F",
            "per_page=100",
        ]
    )
    return {item["title"]: item for item in data}


def create_or_reuse_milestones(milestones: dict[str, Milestone]) -> None:
    existing = list_milestones()
    for milestone in milestones.values():
        match = existing.get(milestone.title)
        if not match:
            cmd = [
                "gh",
                "api",
                f"repos/{REPO}/milestones",
                "-f",
                f"title={milestone.title}",
            ]
            if milestone.description:
                cmd.extend(["-f", f"description={milestone.description}"])
            if milestone.due_on:
                cmd.extend(["-f", f"due_on={github_due_on(milestone.due_on)}"])
            match = gh_json(cmd)
            existing[milestone.title] = match
        milestone.number = int(match["number"])


def create_or_reuse_issues(issues: dict[str, Issue], existing: list[dict[str, Any]]) -> None:
    existing_by_number = {int(item["number"]): item for item in existing}
    for issue in issues.values():
        match = existing_by_number.get(issue.number) if issue.number is not None else None
        if issue.number is None:
            cmd = [
                "gh",
                "issue",
                "create",
                "--repo",
                REPO,
                "--title",
                issue.title,
                "--body-file",
                "-",
            ]
            if issue.milestone:
                cmd.extend(["--milestone", issue.milestone])
            out = run_gh(
                cmd,
                input_text=issue.body,
            )
            url = out.strip().splitlines()[-1]
            number = int(url.rstrip("/").split("/")[-1])
            match = gh_json(
                [
                    "gh",
                    "issue",
                    "view",
                    str(number),
                    "--repo",
                    REPO,
                    "--json",
                    "number,title,url,id",
                ]
            )
            existing_by_number[number] = match
        if match is None:
            raise SystemExit(f"明示されたIssueを再利用できません: #{issue.number}")
        issue.number = int(match["number"])
        issue.url = match["url"]
        issue.node_id = match["id"]


def set_issue_milestones(issues: dict[str, Issue]) -> None:
    for issue in issues.values():
        if issue.milestone and issue.number:
            run_gh(
                [
                    "gh",
                    "issue",
                    "edit",
                    str(issue.number),
                    "--repo",
                    REPO,
                    "--milestone",
                    issue.milestone,
                ]
            )


def link_issue_relations(issues: dict[str, Issue]) -> None:
    for issue in issues.values():
        if issue.parent:
            parent = issues[issue.parent]
            mutation = (
                "mutation { "
                f"addSubIssue(input:{{issueId:{gql_string(parent.node_id or '')},"
                f"subIssueId:{gql_string(issue.node_id or '')},replaceParent:true}}) "
                "{ clientMutationId } "
                "}"
            )
            graphql_json(mutation, duplicate_operation="sub-issue")

    for issue in issues.values():
        for blocker_title in issue.blocked_by:
            blocker = issues[blocker_title]
            mutation = (
                "mutation { "
                f"addBlockedBy(input:{{issueId:{gql_string(issue.node_id or '')},"
                f"blockingIssueId:{gql_string(blocker.node_id or '')}}}) "
                "{ clientMutationId } "
                "}"
            )
            graphql_json(mutation, duplicate_operation="blocked-by")


def project_items_by_url(data: dict[str, Any]) -> dict[str, str]:
    items = data.get("items", [])
    total_count = data.get("totalCount")
    if not isinstance(total_count, int) or total_count > len(items):
        raise SystemExit(f"Project item一覧を全件取得できません: {len(items)} / {total_count}")
    return {
        item["content"]["url"]: item["id"]
        for item in items
        if item.get("content") and item["content"].get("url")
    }


def add_project_items(issues: dict[str, Issue]) -> None:
    for issue in issues.values():
        mutation = (
            "mutation { "
            f"addProjectV2ItemById(input:{{projectId:{gql_string(PROJECT_ID)},"
            f"contentId:{gql_string(issue.node_id or '')}}}) "
            "{ item { id } } "
            "}"
        )
        data = graphql_json(mutation, duplicate_operation="project-item")
        item = data and data.get("data", {}).get("addProjectV2ItemById", {}).get("item")
        if item:
            issue.item_id = item["id"]

    if any(issue.item_id is None for issue in issues.values()):
        data = gh_json(
            [
                "gh",
                "project",
                "item-list",
                PROJECT_NUMBER,
                "--owner",
                OWNER,
                "--format",
                "json",
                "--limit",
                "1000",
            ]
        )
        by_url = project_items_by_url(data)
        for issue in issues.values():
            issue.item_id = issue.item_id or by_url.get(issue.url or "")

    missing = [issue.title for issue in issues.values() if not issue.item_id]
    if missing:
        raise SystemExit(f"Project item idが見つかりません: {missing}")


def field_lookup(
    fields: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    field_ids = {name: field_data["id"] for name, field_data in fields.items()}
    option_ids: dict[tuple[str, str], str] = {}
    for name, field_data in fields.items():
        for option in field_data.get("options", []):
            option_ids[(name, option["name"])] = option["id"]
    return field_ids, option_ids


def field_values(issue: Issue) -> list[tuple[str, FieldKind, str]]:
    return [
        ("Status", "single", issue.status),
        ("Type", "single", issue.type),
        ("Priority", "single", issue.priority),
        ("Size", "single", issue.size),
        ("Complexity", "single", issue.complexity),
        ("Risk", "single", issue.risk),
        ("Agent Tier", "single", issue.agent_tier),
        ("Source", "single", issue.source),
        ("Scope", "text", issue.scope),
        ("Reviewer Owner", "text", issue.reviewer_owner),
        ("Forecast Start", "date", issue.forecast_start),
        ("Forecast End", "date", issue.forecast_end),
    ]


def value_literal(
    kind: FieldKind, value: str, field_name: str, option_ids: dict[tuple[str, str], str]
) -> str:
    if kind == "single":
        return f"{{singleSelectOptionId:{gql_string(option_ids[(field_name, value)])}}}"
    if kind == "text":
        return f"{{text:{gql_string(value)}}}"
    if kind == "date":
        return f"{{date:{gql_string(value)}}}"
    raise ValueError(kind)


def set_project_fields(issues: dict[str, Issue], fields: dict[str, dict[str, Any]]) -> None:
    field_ids, option_ids = field_lookup(fields)
    for issue in issues.values():
        mutations = []
        for idx, (field_name, kind, value) in enumerate(field_values(issue)):
            if not value:
                continue
            mutations.append(
                f"m{idx}:updateProjectV2ItemFieldValue(input:{{"
                f"projectId:{gql_string(PROJECT_ID)},"
                f"itemId:{gql_string(issue.item_id or '')},"
                f"fieldId:{gql_string(field_ids[field_name])},"
                f"value:{value_literal(kind, value, field_name, option_ids)}"
                "}){projectV2Item{id}}"
            )
        if mutations:
            graphql_json(f"mutation {{ {' '.join(mutations)} }}")


def project_field_plan(
    project_fields: list[dict[str, Any]],
    current_fields: dict[str, dict[str, Any]],
    *,
    update_existing: bool,
    allow_option_removal: bool = False,
) -> tuple[list[dict[str, str]], list[str]]:
    actions: list[dict[str, str]] = []
    blockers: list[str] = []
    for desired in project_fields:
        current = current_fields.get(desired["name"])
        if not current:
            actions.append({"field": desired["name"], "action": "create"})
            continue
        if current.get("dataType") != desired["type"]:
            blockers.append(
                f"{desired['name']}: type {current.get('dataType')} != {desired['type']}"
            )
            continue
        action = "noop"
        if desired["type"] == "SINGLE_SELECT":
            try:
                materialized = materialize_single_select_options(
                    desired.get("options", []),
                    current.get("options", []),
                    allow_removal=allow_option_removal,
                )
            except SystemExit as exc:
                blockers.append(f"{desired['name']}: {exc}")
                continue
            if option_signatures(materialized) != option_signatures(current.get("options", [])):
                if update_existing:
                    removed = set(option_names(current.get("options", []))) - set(
                        option_names(desired.get("options", []))
                    )
                    action = (
                        "replace-options-on-empty-project"
                        if removed
                        else "update-preserving-option-ids"
                    )
                else:
                    blockers.append(
                        f"{desired['name']}: option差分。"
                        "apply --update-existing-fieldsで明示してください"
                    )
                    continue
        actions.append({"field": desired["name"], "action": action})
    return actions, blockers


def build_bootstrap_plan(context: dict[str, Any], *, update_existing: bool) -> dict[str, Any]:
    field_actions, blockers = project_field_plan(
        context["project_fields"],
        context["current_fields"],
        update_existing=update_existing,
        allow_option_removal=context["target"]["project"]["items"]["totalCount"] == 0,
    )
    existing_numbers = {int(item["number"]) for item in context["existing_issues"]}
    issue_actions = [
        {
            "title": issue.title,
            "action": "reuse" if issue.number in existing_numbers else "create",
            "number": issue.number,
        }
        for issue in context["issues"].values()
    ]
    existing_milestones = set(list_milestones())
    milestone_actions = [
        {
            "title": milestone.title,
            "action": "reuse" if milestone.title in existing_milestones else "create",
        }
        for milestone in context["milestones"].values()
    ]
    target = context["target"]
    return {
        "mode": "plan",
        "target": {
            "repository": target["repository"]["nameWithOwner"],
            "default_branch": target["repository"]["defaultBranchRef"]["name"],
            "project_number": target["project"]["number"],
            "project_url": target["project"]["url"],
        },
        "field_actions": field_actions,
        "milestone_actions": milestone_actions,
        "issue_actions": issue_actions,
        "relation_count": sum(
            bool(issue.parent) + len(issue.blocked_by) for issue in context["issues"].values()
        ),
        "blockers": blockers,
    }


def relation_issue_numbers(value: Any) -> set[int]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {
            int(item["number"])
            for item in value
            if isinstance(item, dict) and item.get("number") is not None
        }
    if isinstance(value, dict):
        if value.get("number") is not None:
            return {int(value["number"])}
        for key in ("nodes", "issues"):
            if key in value:
                return relation_issue_numbers(value[key])
    return set()


def verify_bootstrap(context: dict[str, Any]) -> dict[str, Any]:
    issues: dict[str, Issue] = context["issues"]
    missing_numbers = [issue.title for issue in issues.values() if issue.number is None]
    if missing_numbers:
        raise SystemExit(
            f"verifyにはapply出力のIssue numberをISSUESへ保存してください: {missing_numbers}"
        )

    current_fields = list_project_fields()
    field_actions, field_blockers = project_field_plan(
        context["project_fields"], current_fields, update_existing=False
    )
    if field_blockers or any(action["action"] != "noop" for action in field_actions):
        raise SystemExit(f"Project field検証に失敗しました: {field_blockers or field_actions}")

    milestones = list_milestones()
    milestone_errors: list[str] = []
    for expected in context["milestones"].values():
        actual = milestones.get(expected.title)
        if not actual:
            milestone_errors.append(f"missing milestone: {expected.title}")
        elif expected.due_on and not str(actual.get("due_on", "")).startswith(expected.due_on):
            milestone_errors.append(f"due date mismatch: {expected.title}")

    existing_by_number = {
        int(item["number"]): item for item in list_issues() if item.get("number") is not None
    }
    issue_errors: list[str] = []
    relation_errors: list[str] = []
    for issue in issues.values():
        actual = existing_by_number.get(issue.number or 0)
        if not actual or actual.get("title") != issue.title or actual.get("url") != issue.url:
            issue_errors.append(f"Issue identity mismatch: {issue.title} #{issue.number}")
            continue
        relation_data = gh_json(
            [
                "gh",
                "issue",
                "view",
                str(issue.number),
                "--repo",
                REPO,
                "--json",
                "number,parent,blockedBy",
            ]
        )
        expected_parent = {issues[issue.parent].number} if issue.parent else set()
        actual_parent = relation_issue_numbers(relation_data.get("parent"))
        if actual_parent != expected_parent:
            relation_errors.append(
                f"parent mismatch: #{issue.number} {actual_parent} != {expected_parent}"
            )
        expected_blockers = {issues[title].number for title in issue.blocked_by}
        actual_blockers = relation_issue_numbers(relation_data.get("blockedBy"))
        if actual_blockers != expected_blockers:
            relation_errors.append(
                f"blockedBy mismatch: #{issue.number} {actual_blockers} != {expected_blockers}"
            )

    items = gh_json(
        [
            "gh",
            "project",
            "item-list",
            PROJECT_NUMBER,
            "--owner",
            OWNER,
            "--format",
            "json",
            "--limit",
            "1000",
        ]
    )
    item_urls = set(project_items_by_url(items))
    missing_items = [issue.url for issue in issues.values() if issue.url not in item_urls]
    errors = milestone_errors + issue_errors + relation_errors
    if missing_items:
        errors.append(f"missing Project items: {missing_items}")
    if errors:
        raise SystemExit(f"bootstrap verify failed: {errors}")
    return {
        "verified": True,
        "field_count": len(context["project_fields"]),
        "milestone_count": len(context["milestones"]),
        "issue_count": len(issues),
        "relation_count": sum(
            bool(issue.parent) + len(issue.blocked_by) for issue in issues.values()
        ),
    }


def prepare_bootstrap() -> dict[str, Any]:
    validate_configuration()
    issues = index_issues(ISSUES)
    milestones = ensure_milestone_plan(MILESTONES)
    ensure_issue_plan(issues, milestones)
    ensure_issue_bodies(issues)
    project_fields = load_project_fields(PROJECT_FIELDS_PATH)
    target = discover_target()
    existing_issues = list_issues()
    validate_issue_reuse(issues, existing_issues)
    hydrate_explicit_issues(issues, existing_issues)
    return {
        "issues": issues,
        "milestones": milestones,
        "project_fields": project_fields,
        "current_fields": list_project_fields(),
        "existing_issues": existing_issues,
        "target": target,
    }


def apply_bootstrap(context: dict[str, Any], *, update_existing: bool) -> dict[str, Any]:
    issues: dict[str, Issue] = context["issues"]
    milestones: dict[str, Milestone] = context["milestones"]
    fields = ensure_project_fields(
        context["project_fields"],
        update_existing=update_existing,
        allow_empty_project_option_migration=True,
    )
    create_or_reuse_milestones(milestones)
    create_or_reuse_issues(issues, context["existing_issues"])
    set_issue_milestones(issues)
    link_issue_relations(issues)
    add_project_items(issues)
    set_project_fields(issues, fields)
    verification = verify_bootstrap(context)
    return {
        "verification": verification,
        "issues": [
            {
                "title": issue.title,
                "number": issue.number,
                "url": issue.url,
                "item_id": issue.item_id,
            }
            for issue in issues.values()
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="read-onlyの変更計画をJSONで表示する")
    plan_parser.add_argument("--update-existing-fields", action="store_true")
    apply_parser = subparsers.add_parser("apply", help="確認済み計画を適用してverifyする")
    apply_parser.add_argument("--update-existing-fields", action="store_true")
    apply_parser.add_argument(
        "--confirm",
        required=True,
        help="誤対象防止のため OWNER/REPO#PROJECT_NUMBER を指定する",
    )
    subparsers.add_parser("verify", help="保存済みIssue numberを使って実状態を検証する")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    context = prepare_bootstrap()
    if args.command == "verify":
        result = verify_bootstrap(context)
    else:
        update_existing = bool(args.update_existing_fields)
        plan = build_bootstrap_plan(context, update_existing=update_existing)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        if args.command == "plan":
            return
        if plan["blockers"]:
            raise SystemExit(f"applyを停止しました: {plan['blockers']}")
        expected_confirmation = f"{REPO}#{PROJECT_NUMBER}"
        if args.confirm != expected_confirmation:
            raise SystemExit(
                f"確認文字列が一致しません: {args.confirm!r} != {expected_confirmation!r}"
            )
        result = apply_bootstrap(context, update_existing=update_existing)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
