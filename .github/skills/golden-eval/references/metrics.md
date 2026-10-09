# Golden-eval metrics

These numbers come from two offline commands: `python eval/eval.py --retrieval-only --json` and `python eval/eval.py --recorded --json`. Neither calls the network.

## recall@5 (`recall_found`)

How many of the expected documents for in-scope golden questions appear in the top five retrieved chunks. A drop usually means the index, chunker, or embeddings changed so the right policy is no longer in the first page of results. Adding a document can displace another by one or two; that is still a recall movement and should be explained, not ignored.

## superseded-document count (`superseded_above_current`)

How many superseded-trap questions rank `DUE-OLD` above the current `DUE-STD`. A rise means the retriever is preferring the contradicted v2.1 standard. That is a grounding failure waiting to happen: answers will cite 24-month Tier 1 reassessment or SOC 2 Type I as if they were current.

## in-scope / out-of-scope score gap

`in_scope_min_top_score` vs `out_of_scope_max_top_score`. In-scope questions should score higher than questions the corpus does not cover. A shrinking gap, or an out-of-scope top score above the weakest in-scope score, usually means the retriever is over-confident on refuse cases or under-confident on real policy questions.

## grounded count (`grounded`)

How many recorded answers still verify as grounded after running today's citation extractor against the recorded retrieved ids. A drop means citation extraction or verification now misses ids that appear in the answer text, or treats a cited id as unsupported. Newly ungrounded question ids are the debugging list: they tell you which answers the verifier stopped trusting.
