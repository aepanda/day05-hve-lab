---
name: eval-regression
description: "Run policy-desk's golden question set and summarize retrieval or grounding regressions. Use after changes to retrieval, chunking, agent instructions, or citation handling."
---

# Eval Regression

Runs policy-desk's golden question set and summarizes regressions.

## When to use

Use after any change to retrieval, chunking, the agent instructions, or citation handling.

## Steps

1. Run `python eval/eval.py --retrieval-only` and record `recall@5`.
2. Run `python eval/eval.py --recorded` and record the grounded-answer count.
3. Compare both numbers with the previous run's numbers in the conversation or in `LAB-LOG.md`. Report any drop, with the question ids that changed.
