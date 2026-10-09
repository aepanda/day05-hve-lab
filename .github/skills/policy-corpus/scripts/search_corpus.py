#!/usr/bin/env python3
"""Lexical search over policy-desk corpus sections. Standard library only."""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HEADING_RE = re.compile(r"^#{2,3}\s+.+$|^\*\*[^*\n]{3,80}\.\*\*", re.MULTILINE)
META_RE = re.compile(r"^(Doc ID|Version|Owner|Effective|Status):\s*(.+?)\s*$", re.MULTILINE)
TOKEN_RE = re.compile(r"[a-z0-9]+")
SECTION_NUM_RE = re.compile(
    r"^(?:section\s+)?(\d+(?:\.\d+)*)(?:[.\s:.—–-]+|$)|step\s+(\d+)\s*:",
    re.IGNORECASE,
)


def repo_root() -> Path:
    start = Path.cwd().resolve()
    candidates = [start, *start.parents, *Path(__file__).resolve().parents]
    seen: set[Path] = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        if (p / "pyproject.toml").is_file() and (p / "corpus").is_dir():
            return p
    sys.exit("Could not find the policy-desk repository root (pyproject.toml + corpus/).")


@dataclass
class Section:
    doc_id: str
    version: str
    status: str
    file: Path
    line: int
    heading: str
    number: str | None
    text: str
    tokens: list[str]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def heading_label(raw: str) -> str:
    line = raw.strip()
    if line.startswith("#"):
        return re.sub(r"^#+\s*", "", line).strip()
    return line.strip("* ").rstrip(".")


def section_number(heading: str) -> str | None:
    match = SECTION_NUM_RE.search(heading.strip())
    if not match:
        return None
    return match.group(1) or match.group(2)


def parse_document(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    meta = {key: value for key, value in META_RE.findall(raw[:800])}
    return meta, raw


def make_section(path: Path, meta: dict[str, str], raw: str, start: int, end: int, heading: str) -> Section:
    text = raw[start:end]
    return Section(
        doc_id=meta.get("Doc ID", path.stem),
        version=meta.get("Version", "?"),
        status=meta.get("Status", "Current"),
        file=path,
        line=raw[:start].count("\n") + 1,
        heading=heading,
        number=section_number(heading),
        text=text,
        tokens=tokenize(text),
    )


def sections_from(path: Path, meta: dict[str, str], raw: str) -> list[Section]:
    marks = list(HEADING_RE.finditer(raw))
    if not marks:
        title = next((ln[2:].strip() for ln in raw.splitlines() if ln.startswith("# ")), path.stem)
        return [make_section(path, meta, raw, 0, len(raw), title)]
    sections: list[Section] = []
    if marks[0].start() > 0 and raw[: marks[0].start()].strip():
        sections.append(make_section(path, meta, raw, 0, marks[0].start(), "Preamble"))
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        sections.append(make_section(path, meta, raw, mark.start(), end, heading_label(mark.group(0))))
    return sections


def load_sections(corpus: Path) -> list[Section]:
    sections: list[Section] = []
    for path in sorted(corpus.glob("*.md")):
        if path.name == "MANIFEST.md":
            continue
        meta, raw = parse_document(path)
        sections.extend(sections_from(path, meta, raw))
    return sections


def bm25_scores(query: list[str], sections: list[Section], k1: float = 1.5, b: float = 0.75) -> list[float]:
    n = len(sections)
    df: Counter[str] = Counter()
    for sec in sections:
        df.update(set(sec.tokens))
    avgdl = sum(len(s.tokens) for s in sections) / max(n, 1)
    idf = {t: math.log(1 + (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5)) for t in set(query)}
    scores = []
    qset = set(query)
    for sec in sections:
        tf = Counter(sec.tokens)
        dl = len(sec.tokens) or 1
        score = 0.0
        for term in qset:
            freq = tf.get(term, 0)
            if not freq:
                continue
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf[term] * (freq * (k1 + 1)) / denom
        # Prefer sections that keep query phrases together (Type I, SOC 2).
        hay = " ".join(sec.tokens)
        needle = " ".join(query)
        if needle and needle in hay:
            score += 2.0
        scores.append(score)
    return scores


def citation_key(sec: Section) -> str:
    if sec.number:
        return f"{sec.doc_id} §{sec.number}"
    return f"{sec.doc_id} ({sec.heading})"


def snippet(text: str, width: int = 180) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= width else compact[: width - 1] + "…"


def is_current(status: str) -> bool:
    return status.strip().lower() == "current"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search terms")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--include-superseded", action="store_true")
    args = parser.parse_args()
    query_tokens = tokenize(args.query)
    if not query_tokens:
        print("empty query")
        return 1

    root = repo_root()
    sections = load_sections(root / "corpus")
    scores = bm25_scores(query_tokens, sections)
    ranked = sorted(zip(scores, sections), key=lambda x: x[0], reverse=True)

    current_hits: list[tuple[float, Section]] = []
    superseded_hits: list[Section] = []
    seen_superseded: set[str] = set()
    for score, sec in ranked:
        if score <= 0:
            break
        if is_current(sec.status):
            current_hits.append((score, sec))
        elif sec.doc_id not in seen_superseded:
            seen_superseded.add(sec.doc_id)
            superseded_hits.append(sec)

    if superseded_hits:
        for sec in superseded_hits:
            print(f"SUPERSEDED, do not cite: {sec.doc_id} ({sec.status}) {sec.file.name}")
            if args.include_superseded:
                rel = sec.file.relative_to(root)
                print(f"  {citation_key(sec)}  {sec.heading}  v{sec.version}  {rel}:{sec.line}")
                print(f"  {snippet(sec.text)}")

    shown = current_hits[: args.top]
    if not shown:
        print(f"no current corpus section matched: {args.query!r}")
        return 1

    for score, sec in shown:
        rel = sec.file.relative_to(root)
        print(f"{citation_key(sec)}")
        print(f"  heading: {sec.heading}")
        print(f"  doc_id: {sec.doc_id}  version: {sec.version}  status: {sec.status}")
        print(f"  {rel}:{sec.line}")
        print(f"  {snippet(sec.text)}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
