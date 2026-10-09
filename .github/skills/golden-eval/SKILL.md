---
name: golden-eval
description: "Detect policy-desk evaluation regressions by running the offline golden retrieval and recorded-answer checks and comparing them to a saved baseline. Use when citation verification, retrieval, chunking, the agent, or answer quality may have changed, or when asked whether eval metrics or answer quality regressed."
---

# Golden eval

Deterministic regression check for policy-desk. The model decides when to run it; the script decides whether quality moved.

## When to use

After a change to `src/policy_desk/citations.py`, retrieval, chunking, the agent instructions, the corpus, or the index. Also when someone asks whether answer quality or eval metrics regressed.

Do not use for unrelated code-explanation questions.

## Commands

From the repository root (the script finds the root even if the shell is elsewhere):

```bash
python .github/skills/golden-eval/scripts/compare_eval.py
```

Save a new baseline only after the user confirms. A baseline taken after a regression hides the regression.

```bash
python .github/skills/golden-eval/scripts/compare_eval.py --save-baseline
```

Ask before running `--save-baseline`. Never save a baseline unprompted.

## How to report

- Print the script's metric lines (old → new, delta).
- Exit 0 means no regression against the saved baseline.
- Exit 1 means a regression: recall dropped, superseded-document count rose, or grounded count dropped. Name any question ids that are newly not grounded.
- Exit 2 means there is no baseline yet.

Metric definitions live in [references/metrics.md](references/metrics.md). Read that file when you need to explain what a movement means; do not inline the definitions here.
