---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/component_repair_targets.csv
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/future_extractor_schema.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv
  - work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/raw_pressure_two_tap_harvest.csv
tags: [pressure-ledger, two-tap, component-k, extractor]
related:
  - .agent/status/2026-07-17_AGENT-530.md
  - imports/2026-07-17_two_tap_component_repair_extractor.json
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md
task: AGENT-530
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Component Repair Extractor

Task: AGENT-530

## Attempted

Implemented the AGENT-525 future extractor schema using existing preserved and
staged evidence only. The extractor targets the three `corner_lower_right`
Salt2/3/4 rows selected by AGENT-525 and emits a table that a later raw
postprocessor can replace with finite endpoint-pressure and recirculation
fields.

## Observed

The extractor emitted 3 rows and 15 failed gate rows. Current evidence supports
time labels, hydrostatic/dynamic corrections, centerline straight-reference
subtraction, dynamic-pressure normalization, `K_apparent`, and current
centerline `K_local`. It does not support local feature `p_upstream_pa`,
`p_downstream_pa`, RAF, RMF, SVF, or same-QOI mesh/time uncertainty. The current
centerline `K_local` values are negative for all three target rows.

## Inferred

The immediate next work is not fitting or coefficient export. It is raw
postprocessing for local feature endpoint pressure surfaces and same-window flow
diagnostics. The extractor clarifies exactly what is missing and keeps the rows
machine-readable for the later postprocessor.

## Contradictions And Caveats

No raw OpenFOAM sampling was launched. Blank endpoint and recirculation fields
are intentional blockers. Negative K was not clipped and no universal K/global
friction multiplier was inferred.

## Next Useful Actions

Use `next_raw_postprocessing_queue.csv` to claim a separate staged-copy
postprocessing task. That task should sample `corner_lower_right` upstream and
downstream feature taps for Salt2/Salt3/Salt4, emit pressure basis and velocity
basis fields, compute same-window RAF/RMF/SVF, and attach same-QOI uncertainty
or a non-GCI uncertainty flag.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, or active-agent scoped
artifacts were mutated. No solver/postprocessing launch, fitting, tuning, model
selection, or scientific admission change was performed.
