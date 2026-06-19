from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "node_modules"}


def test_assets_python_files_have_sibling_tests() -> None:
    missing_tests: list[str] = []

    for path in sorted(REPO_ROOT.rglob("*.py")):
        relative_parts = path.relative_to(REPO_ROOT).parts
        if any(part in IGNORED_DIRS for part in relative_parts):
            continue
        if "assets" not in relative_parts or path.name.startswith("test_"):
            continue

        expected = path.with_name(f"test_{path.stem.replace('-', '_')}.py")
        if not expected.exists():
            missing_tests.append(f"{path.relative_to(REPO_ROOT)} -> {expected.name}")

    assert not missing_tests, "missing sibling asset tests:\n" + "\n".join(missing_tests)
