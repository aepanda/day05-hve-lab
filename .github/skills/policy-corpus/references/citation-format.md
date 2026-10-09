# Northwind policy citation format

## Citable form

Every claim taken from the corpus cites:

- **Doc ID and section**, for example `DUE-STD §4.2` or `TIER-MTX §3`. An unnumbered heading is cited as `GIFT-POL` plus the heading (`Gifts`).
- **Version** from the document's `Version:` line.
- **file:line** so a reviewer can open the section (`corpus/due-diligence-standard.md:29`).

Example: `DUE-STD §4.2 (v3.0, corpus/due-diligence-standard.md:29)`.

## Only Current documents

A document whose `Status` is not `Current` is not a requirement. `DUE-OLD` is lexically close to `DUE-STD` and will match many due-diligence queries. Mention it only as superseded. Cite `DUE-STD` unless the user explicitly asks about v2.1.

## Why

Policy answers are only as good as the version they rest on. Section and version stop a 24-month Tier 1 cycle or a SOC 2 Type I acceptance from slipping in from the old standard. file:line makes the citation checkable without re-running search.
