---
provenance:
  task: AGENT-346
  owner: codex
  created_at: 2026-07-14T14:31:00-05:00
tags: [journal, cfd-pp, submitted-runs, lineage, corrected-q]
related:
  - .agent/status/2026-07-14_AGENT-346.md
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/README.md
---
# Submitted CFD Run Compact Lineage Table

## Request

The coordinator asked for a more compact version of `submitted_cfd_run_steady_state_table.csv` where lineages are collapsed and only the latest same-Q run is reported. Changed-Q cases are different physical runs and must remain separate.

## Method

Implemented `tools/analyze/build_submitted_cfd_run_compact_lineage_table.py`.

The script consumes:

- `work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv`

It emits:

- `submitted_cfd_run_compact_lineage_table.csv`
- `compact_lineage_summary.json`

Collapse rule:

- Collapse same-Q continuation rows to the row with the latest available last-window/end time.
- Keep changed-Q rows separate: `lo10q`, `hi10q`, `lo5q`, `hi5q`, legacy `loq`, and legacy `hiq`.
- Preserve the hidden rows in `collapsed_from_run_keys` and `superseded_run_keys`.
- Preserve non-Q scenario suffixes like `optins`, `hiins`, `loins`, `loH`, and `hiH` as separate contexts unless explicit continuation evidence makes them the same lineage.

## Results

- Full source rows: 50.
- Compact lineage rows: 47.
- Collapsed rows: 3.
- Lineages with superseded rows: 2.

Important row:

- `salt1_jin::nominal` now reports `salt1_jin_nominal_continuation_corrected` as latest.
- It collapses `salt1_jin` and `salt1_jin_basecont` into `superseded_run_keys`.
- Salt1 `lo10q` and `hi10q` remain separate rows.

## Verification

Passed:

- `python3.11 -m unittest tools.analyze.test_submitted_cfd_run_compact_lineage_table`
- `python3.11 tools/analyze/build_submitted_cfd_run_compact_lineage_table.py`

Native CFD solver outputs were not mutated. Generated repo index files were intentionally left untouched because active AGENT-344 owns the generated index scope.
