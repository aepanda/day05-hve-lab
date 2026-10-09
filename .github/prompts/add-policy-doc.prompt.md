---
description: "Add a policy document to the corpus: validate metadata, register it, rebuild the index, and check retrieval recall."
argument-hint: "docPath=<path-to-new-policy.md>"
agent: agent
---

# Add a policy document safely

The document to add is `${input:docPath}`. Keep the current manifest in context: #file:../../corpus/MANIFEST.md

Do not commit. Stop and report after the procedure. If `${input:docPath}` appears literally (the prompt text was pasted instead of `/add-policy-doc`), ask for the file path and stop.

## Procedure

1. Read `${input:docPath}`. Refuse and stop, without changing files, if any of these is true:
   - the file does not start with the metadata block every corpus document uses: a `# Title` line, then `Doc ID`, `Version`, `Owner`, `Effective`, and `Status` lines;
   - the Doc ID already exists in `corpus/MANIFEST.md`.

2. From the repository root, before changing anything, run `python eval/eval.py --retrieval-only --json` and keep the JSON as the before snapshot.

3. Copy the file into `corpus/` with a kebab-case file name (lowercase words from the title, hyphen-separated, `.md`). Refuse if that path already exists.

4. Count words as whitespace-delimited tokens over the full file, including the metadata block. Add a row to the manifest table:

   `| Doc ID | File | Title | Status | Words |`

   Then update the `Total:` line below the table with the new document count and word sum.

5. Run `python -m policy_desk.build_index` from the repository root.

6. Run `pytest`, then `python eval/eval.py --retrieval-only --json` again. Report `recall_found` / `recall_total` before and after, plus the pytest result.

7. Stop. Do not commit. Summarize the copied path, Doc ID, word count, and recall before and after.
