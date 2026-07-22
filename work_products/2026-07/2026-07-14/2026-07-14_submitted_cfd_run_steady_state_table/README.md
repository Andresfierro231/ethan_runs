---
provenance:
  task: AGENT-343
  generated_by: tools/analyze/build_submitted_cfd_run_steady_state_table.py
tags: [cfd-pp, cfd-runs, steady-state, corrected-q, continuation]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv
---
# Submitted CFD Run Steady-State Table

## Scope

This package consolidates submitted CFD solver rows from the known submission ledgers and joins them to existing last-window steady-state detection outputs. It includes continuations, water validation rows, legacy diagnostic perturbations, and corrected/perturbed Salt-Q rows.

## Label Rule

- `steady`: an explicit final-window or time-series detector found the representative last window steady/quasi-steady without drifting series.
- `needs continuation`: the row is running, drifting, under-advanced, failed/not accepted, or lacks a terminal current-run steady window.
- `not run`: a submitted/registered row was found but no last-window detector output was found.

Admission is not the same as this label. For example, Salt1 corrected-Q rows can be `steady` by final-window flatness while still diagnostic for fit use until Salt1 policy/admission resolves.

## Results

- Rows: `50`
- Label counts: `{"needs continuation": 33, "not run": 3, "steady": 14}`
- Rows with detector output: `43`
- Rows without detector output: `7`

## Files

- `submitted_cfd_run_steady_state_table.csv`: full table requested by the coordinator.
- `submitted_cfd_run_compact_lineage_table.csv`: compact lineage-collapsed table. Same-Q continuations are collapsed to the latest row; changed-Q rows remain separate physical runs.
- `submitted_cfd_run_summary.csv`: counts by fluid, variant, and steady label.
- `compact_lineage_summary.json`: compact table generation summary.
- `source_manifest.csv`: exact input/output paths.

## Compact Lineage Table

The compact table keeps changed-Q rows separate. For example, `lo10q`,
`hi10q`, `lo5q`, `hi5q`, legacy `loq`, and legacy `hiq` are not merged into
nominal rows. Same-Q continuation windows are collapsed to the latest available
run and the hidden parent rows are preserved in `collapsed_from_run_keys` and
`superseded_run_keys`.

Current compact result:

- Full rows: `50`
- Compact lineage rows: `47`
- Collapsed rows: `3`
- Lineages with superseded rows: `2`

The Salt1 nominal lineage is reported as:

- `lineage_group`: `salt1_jin::nominal`
- `latest_run_key`: `salt1_jin_nominal_continuation_corrected`
- `superseded_run_keys`: `salt1_jin;salt1_jin_basecont`
