---
name: policy-corpus
description: "Locate and cite Northwind Capital Group third-party risk policy documents in corpus/. Use during research and planning when a task depends on what a Northwind policy requires (vendor tier, due diligence, SOC 2, reassessment, offshoring, procurement). Run the bundled search script and return source pointers (doc id, section, version, file:line) for the phase to verify; write nothing."
---

# policy-corpus

Northwind's TPRM and procurement rules live in `corpus/*.md`. This skill adds those sources to `rpi-research` and `rpi-plan`. It does not change either phase's process, write paths, or decisions.

## When the phase should call it

A research or planning task that depends on what a Northwind policy requires: vendor tier, due diligence evidence, SOC 2, reassessment frequency, offshoring, gifts, access, incidents, or procurement.

## How to search

From the repository root:

```bash
python .github/skills/policy-corpus/scripts/search_corpus.py "<query>" --top 5
```

Run several narrow queries rather than one broad one. After the script returns a hit, read the section at the printed `corpus/<file>:<line>` before relying on it. Treat script output as pointers, not as verified findings.

## Citations

Follow [references/citation-format.md](references/citation-format.md). Cite `Doc ID §section` with version and `file:line`. Only `Status: Current` documents are citable.

## Superseded matches

If the script prints `SUPERSEDED, do not cite`, name that document as a trap, do not use it as a requirement, and read the current replacement instead (`DUE-OLD` is replaced by `DUE-STD`).

## Authority

Return source pointers for the phase to verify. Write nothing. Do not invent policy.
