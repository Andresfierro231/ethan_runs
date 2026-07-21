---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/cfd_postprocessing_schema_gap_audit.csv
tags: [board-dispatch, schema-gap, cfd-postprocessing]
related:
  - .agent/status/2026-07-21_TODO-LITREV-SCHEMA-GAP-BOARD-FOLLOWONS-2026-07-21.md
  - imports/2026-07-21_litrev_schema_gap_board_followons.json
task: TODO-LITREV-SCHEMA-GAP-BOARD-FOLLOWONS-2026-07-21
date: 2026-07-21
role: Coordinator/Writer
type: journal
status: complete
---
# LitRev Schema-Gap Board Followons

## Attempted

Converted the schema-gap audit's uncovered next actions into claimable board
rows.

## Observed

The board already had coverage for several related lanes:

- `TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY` is complete.
- `TODO-LITREV-THERMAL-HEAT-LOSS-CONTRACT-ALIGNMENT` is complete.
- Recirculation switching and single-stream developing precheck rows remain
  open.

The missing board coverage was at the execution/readiness layer: pressure
metadata standardization, matched-plane recirculation field harvest, same-QOI
UQ execution, split-junction/storage/radiation extraction, and latest live-run
schema promotion.

## Inferred

These new rows are intentionally narrower than a broad postprocessing wave.
They each preserve current guardrails: no native source-output mutation, no
duplicate solver launch, no coefficient admission, and no runtime leakage.

## Next Useful Actions

Workers can claim one row at a time. The highest-priority technical unlock is
`TODO-LITREV-SAME-QOI-UQ-EXECUTION`, because pressure, F6, and thermal
coefficient admissions all remain blocked without same-basis uncertainty.
