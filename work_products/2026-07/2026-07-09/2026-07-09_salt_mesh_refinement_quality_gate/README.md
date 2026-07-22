# Salt Mesh Refinement Quality Gate

Generated: `2026-07-09T09:24:45-05:00`

## Scope

This package implements the first categorization and lightweight postProcessing
quality gate for Ethan's Salt `coarse/`, `medium/`, and `fine` mesh-family
source tree. It is read-only over the source cases and does not stage, register,
reconstruct, or mutate solver outputs.

## Outputs

- `mesh_case_catalog.csv`: all 24 mesh cases with source paths, mesh metadata,
  categorization, admission bucket, and provenance labels.
- `mesh_quality_gate.csv`: log-tail status, convergenceMonitor status,
  postProcessing availability, and gate verdict per case.
- `endpoint_postprocessing_summary.csv`: bounded tail-window summaries from the
  latest restart-segment monitor files for Salt 2 Jin and Salt 4 Jin endpoint
  families.
- `gci_candidate_matrix.csv`: per-QoI triplet readiness for Salt 2/4 Jin.
- `closure_observation_update_recommendations.md`: how future observation-table
  work should consume these results.
- `summary.json`: machine-readable counts and verdict summary.

## Verdict Summary

- Total catalog rows: `24`
- Endpoint summary rows: `48`
- Gate verdict counts: `{'admitted_for_gci_input': 2, 'historical_kirst_only': 12, 'inventory_only': 6, 'partial_needs_coarse_reconciliation': 2, 'partial_needs_continuation': 2}`
- GCI triplet status counts: `{'partial_needs_coarse_reconciliation': 5, 'partial_needs_continuation_or_gate': 5}`

## Interpretation

Salt 2 Jin remains the first mesh-family target: medium and fine are admitted by
this lightweight gate, but the external coarse source is still held for
reconciliation against the repo's current mainline continuation. Salt 4 Jin
remains the required upper endpoint but is partial because medium/fine source
logs tail with signal-15/no clean convergenceMonitor evidence in this gate.
Monitor statistics are screening signals only: large monitor files are parsed
from a bounded tail window of the latest restart segment, not a full reconstructed
history.

Kirst rows remain historical provenance only. No row from this package should be
used directly for closure fitting until a future task updates the canonical
closure-observation contract with explicit mesh uncertainty and fit/validation
flags.
