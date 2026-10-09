#!/usr/bin/env python3
"""Fail CI when Copilot customization frontmatter is broken or unwired."""

from __future__ import annotations

import glob as globlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / ".github"
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)


def glob_matches(pattern: str) -> bool:
    pattern = pattern.strip().strip("'\"")
    if not pattern:
        return False
    for hit in globlib.glob(pattern, root_dir=ROOT, recursive=True):
        path = ROOT / hit
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        return True
    return False


def extract_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, f"{path.relative_to(ROOT)}: missing opening --- frontmatter fence"
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, f"{path.relative_to(ROOT)}: missing closing --- frontmatter fence"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"{path.relative_to(ROOT)}: YAML error: {exc}"
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, f"{path.relative_to(ROOT)}: frontmatter is not a mapping"
    return data, None


def iter_artifacts() -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    if not GITHUB.is_dir():
        return found
    for path in sorted(GITHUB.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".agent.md"):
            found.append(("agent", path))
        elif name.endswith(".prompt.md"):
            found.append(("prompt", path))
        elif name.endswith(".instructions.md") or name == "copilot-instructions.md":
            found.append(("instruction", path))
        elif name == "SKILL.md":
            found.append(("skill", path))
    return found


def tool_names(meta: dict) -> list[str]:
    tools = meta.get("tools") or []
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.strip("[]").split(",") if t.strip()]
    return [str(t) for t in tools]


def agent_list(meta: dict) -> list[str]:
    agents = meta.get("agents") or []
    if isinstance(agents, str):
        agents = [agents]
    return [str(a) for a in agents]


def main() -> int:
    artifacts = iter_artifacts()
    failures: list[str] = []
    parsed: dict[Path, dict] = {}
    agent_names: dict[str, Path] = {}

    for kind, path in artifacts:
        meta, err = extract_frontmatter(path)
        if err:
            failures.append(err)
            continue
        parsed[path] = meta
        if kind in {"agent", "prompt", "instruction"}:
            if not meta.get("description"):
                failures.append(f"{path.relative_to(ROOT)}: missing required field 'description'")
        if kind == "skill":
            name = meta.get("name")
            desc = meta.get("description")
            folder = path.parent.name
            if not name:
                failures.append(f"{path.relative_to(ROOT)}: missing required field 'name'")
            else:
                if name != folder:
                    failures.append(
                        f"{path.relative_to(ROOT)}: name '{name}' does not match folder '{folder}'"
                    )
                if not NAME_RE.match(str(name)):
                    failures.append(
                        f"{path.relative_to(ROOT)}: name '{name}' is not lowercase kebab-case"
                    )
            if not desc:
                failures.append(f"{path.relative_to(ROOT)}: missing required field 'description'")
        if kind == "agent":
            declared = meta.get("name")
            if declared:
                agent_names[str(declared)] = path
        apply_to = meta.get("applyTo")
        if apply_to:
            globs = [g.strip() for g in str(apply_to).split(",") if g.strip()]
            for glob in globs:
                if not glob_matches(glob):
                    failures.append(
                        f"{path.relative_to(ROOT)}: applyTo glob '{glob}' matches no file in the repository"
                    )
        description = str(meta.get("description") or "")
        if kind == "agent" and "read-only" in description.lower():
            bad = [t for t in tool_names(meta) if str(t).startswith(("edit/", "execute/"))]
            if bad:
                failures.append(
                    f"{path.relative_to(ROOT)}: description says read-only but tools include {', '.join(bad)}"
                )

    for path, meta in parsed.items():
        if not path.name.endswith(".agent.md"):
            continue
        for ref in agent_list(meta):
            if ref not in agent_names:
                failures.append(
                    f"{path.relative_to(ROOT)}: agents: '{ref}' does not resolve to an existing agent name"
                )

    rels = [str(p.relative_to(ROOT)) for _, p in artifacts]
    if failures:
        for line in failures:
            print(line)
        print(f"checked {len(artifacts)} artifacts: {len(failures)} failures")
        return 1
    print(f"checked {len(artifacts)} artifacts: 0 failures")
    print("\n".join(f"  {r}" for r in rels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
