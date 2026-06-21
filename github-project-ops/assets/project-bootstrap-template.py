"""github-project-ops用の編集可能なGitHub Project bootstrapテンプレート。

これはそのまま使う丸ごと実行用スクリプトではない。一時パスへコピーし、設定欄を
確認済みのGitHub値へ置き換え、ISSUESを見直してから実行する。

必要なツール:
- リポジトリとprojectスコープで認証済みのgh CLI
- Python 3.10+
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
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


def gh_optional_json(args: list[str]) -> Any | None:
    out = run_gh(args, check=False)
    return json.loads(out) if out.strip() else None


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
    return option_spec.get("description", "")


def has_option_metadata(options: list[OptionSpec]) -> bool:
    return any(
        isinstance(option_spec, dict) and ("color" in option_spec or "description" in option_spec)
        for option_spec in options
    )


def option_names(options: list[OptionSpec]) -> list[str]:
    return [option_name(option_spec) for option_spec in options]


def list_project_fields() -> dict[str, dict[str, Any]]:
    data = gh_json(
        [
            "gh",
            "project",
            "field-list",
            PROJECT_NUMBER,
            "--owner",
            OWNER,
            "--format",
            "json",
            "--limit",
            "100",
        ]
    )
    return {field_data["name"]: field_data for field_data in data["fields"]}


def single_select_option_literals(options: list[OptionSpec]) -> str:
    option_literals = [
        (
            f"{{name:{gql_string(option_name(option_spec))},"
            f"color:{option_color(option_spec, idx)},"
            f"description:{gql_string(option_description(option_spec))}}}"
        )
        for idx, option_spec in enumerate(options)
    ]
    return ",".join(option_literals)


def update_single_select_options(field_id: str, options: list[OptionSpec]) -> None:
    mutation = (
        "mutation { "
        f"updateProjectV2Field(input:{{fieldId:{gql_string(field_id)},"
        f"singleSelectOptions:[{single_select_option_literals(options)}]}}) "
        "{ projectV2Field { ... on ProjectV2SingleSelectField { id name options { id name } } } } "
        "}"
    )
    gh_json(["gh", "api", "graphql", "-f", f"query={mutation}"])


def ensure_project_fields(project_fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    fields = list_project_fields()
    for field_data in project_fields:
        existing = fields.get(field_data["name"])
        options = field_data.get("options", [])
        if existing:
            if field_data["type"] == "SINGLE_SELECT":
                desired_names = option_names(options)
                current = [option["name"] for option in existing.get("options", [])]
                if current != desired_names or has_option_metadata(options):
                    update_single_select_options(existing["id"], options)
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
            update_single_select_options(fields[field_data["name"]]["id"], options)
    return list_project_fields()


def list_issues() -> dict[str, dict[str, Any]]:
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
    return {item["title"]: item for item in data}


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


def create_or_reuse_issues(issues: dict[str, Issue]) -> None:
    existing = list_issues()
    for issue in issues.values():
        match = existing.get(issue.title)
        if not match:
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
            existing[issue.title] = match
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
            gh_optional_json(["gh", "api", "graphql", "-f", f"query={mutation}"])

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
            gh_optional_json(["gh", "api", "graphql", "-f", f"query={mutation}"])


def add_project_items(issues: dict[str, Issue]) -> None:
    for issue in issues.values():
        mutation = (
            "mutation { "
            f"addProjectV2ItemById(input:{{projectId:{gql_string(PROJECT_ID)},"
            f"contentId:{gql_string(issue.node_id or '')}}}) "
            "{ item { id } } "
            "}"
        )
        data = gh_optional_json(["gh", "api", "graphql", "-f", f"query={mutation}"])
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
                "200",
            ]
        )
        by_title = {
            item["content"]["title"]: item["id"]
            for item in data.get("items", [])
            if item.get("content") and item["content"].get("title")
        }
        for issue in issues.values():
            issue.item_id = issue.item_id or by_title.get(issue.title)

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
            gh_json(["gh", "api", "graphql", "-f", f"query=mutation {{ {' '.join(mutations)} }}"])


def main() -> None:
    issues = {issue.title: issue for issue in ISSUES}
    milestones = ensure_milestone_plan(MILESTONES)
    ensure_issue_plan(issues, milestones)
    ensure_issue_bodies(issues)
    project_fields = load_project_fields(PROJECT_FIELDS_PATH)
    fields = ensure_project_fields(project_fields)
    create_or_reuse_milestones(milestones)
    create_or_reuse_issues(issues)
    set_issue_milestones(issues)
    link_issue_relations(issues)
    add_project_items(issues)
    set_project_fields(issues, fields)
    print(
        json.dumps(
            {
                "issue_count": len(issues),
                "item_count": len([issue for issue in issues.values() if issue.item_id]),
                "first_issue": min(issue.number for issue in issues.values() if issue.number),
                "last_issue": max(issue.number for issue in issues.values() if issue.number),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
