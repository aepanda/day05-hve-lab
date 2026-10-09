#!/usr/bin/env python3
"""Compare offline policy-desk eval metrics against a saved baseline.

Run from anywhere; paths resolve from the repository root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
BASELINE = SKILL_DIR / "references" / "baseline.json"


def repo_root() -> Path:
    start = Path.cwd().resolve()
    candidates = [start, *start.parents, *Path(__file__).resolve().parents]
    seen: set[Path] = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        if (p / "pyproject.toml").is_file() and (p / "eval" / "eval.py").is_file():
            return p
    sys.exit("Could not find the policy-desk repository root (pyproject.toml + eval/eval.py).")


def run_eval(root: Path, *flags: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "eval/eval.py", *flags],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(f"eval.py {' '.join(flags)} failed with exit {proc.returncode}")
    return json.loads(proc.stdout)


def collect(root: Path) -> dict:
    retrieval = run_eval(root, "--retrieval-only", "--json")
    recorded = run_eval(root, "--recorded", "--json")
    return {
        "recall_found": retrieval["recall_found"],
        "superseded_above_current": retrieval["superseded_above_current"],
        "in_scope_min_top_score": retrieval.get("in_scope_min_top_score"),
        "out_of_scope_max_top_score": retrieval.get("out_of_scope_max_top_score"),
        "grounded": recorded["grounded"],
        "not_grounded_ids": list(recorded.get("not_grounded_ids") or []),
    }


def fmt(metric: str, old, new) -> str:
    delta = (new or 0) - (old or 0)
    sign = f"{delta:+d}" if isinstance(delta, int) else f"{delta:+.3f}"
    return f"{metric:<30} {old} -> {new}  ({sign})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Write the current metrics to references/baseline.json.",
    )
    args = parser.parse_args()
    root = repo_root()
    current = collect(root)

    if args.save_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")
        print(f"saved baseline to {BASELINE.relative_to(root)}")
        for key in ("recall_found", "superseded_above_current", "grounded"):
            print(f"{key:<30} {current[key]}")
        return 0

    if not BASELINE.is_file():
        print("no baseline yet; run with --save-baseline after confirming the current numbers")
        return 2

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    print(fmt("recall_found", baseline["recall_found"], current["recall_found"]))
    print(fmt("superseded_above_current", baseline["superseded_above_current"], current["superseded_above_current"]))
    print(fmt("grounded", baseline["grounded"], current["grounded"]))

    old_ungrounded = set(baseline.get("not_grounded_ids") or [])
    new_ungrounded = set(current.get("not_grounded_ids") or [])
    newly = sorted(new_ungrounded - old_ungrounded)

    failed = False
    if current["recall_found"] < baseline["recall_found"]:
        failed = True
        print("REGRESSION: recall dropped")
    if current["superseded_above_current"] > baseline["superseded_above_current"]:
        failed = True
        print("REGRESSION: superseded-document count rose")
    if current["grounded"] < baseline["grounded"]:
        failed = True
        print("REGRESSION: grounded count dropped")
    if newly:
        print("newly not grounded: " + ", ".join(newly))
        if current["grounded"] < baseline["grounded"]:
            failed = True

    if failed:
        return 1
    print("OK: no regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
