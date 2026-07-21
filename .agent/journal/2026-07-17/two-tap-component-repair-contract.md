---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/named_pressure_readiness.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv
  - work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/raw_pressure_two_tap_harvest.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/corner_k_gate_matrix.csv
tags: [pressure-ledger, two-tap, component-k, extraction-contract]
related:
  - .agent/status/2026-07-17_AGENT-525.md
  - imports/2026-07-17_two_tap_component_repair_contract.json
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/README.md
task: AGENT-525
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Component Repair Contract

Task: AGENT-525

## Attempted

Implemented the first AGENT-523 pressure-extraction queue item as a concrete
repair contract for future two-tap/component extraction. The package consumes
existing readiness, tap-length, component-K, raw-pressure, and corner-K evidence
only.

## Observed

The nearest repair targets are three `corner_lower_right` rows for Salt2,
Salt3, and Salt4. All remain non-admitted. Centerline tap lengths are available
for these rows, but current centerline straight-reference subtraction produces
negative local K values. The package defines seven required fields and five
acceptance gates before any future K use.

## Inferred

The blocker is now sharper than "need better pressure data." A future extractor
must emit same-window pressure and velocity bases, comparable straight-reference
losses, component-isolation labels, RAF/RMF/SVF masks, and same-QOI mesh/time
uncertainty. Without those fields, even rows that look like the closest K
candidates remain diagnostic.

## Contradictions And Caveats

This package does not run OpenFOAM, repair raw fields, or admit a coefficient.
It also does not make `corner_lower_right` physically correct by selection; it
only identifies those rows as the least-blocked current targets. Negative K
must not be clipped or hidden inside a global multiplier.

## Next Useful Actions

Use `future_extractor_schema.csv` and `acceptance_gate_matrix.csv` when building
the next staged-copy postprocessor. The future extractor should emit one row per
case/feature/time-window with pressure basis, velocity basis, straight-reference
subtraction, K_apparent, K_local, RAF/RMF/SVF, uncertainty, and explicit
admission status.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, or active-agent scoped
artifacts were mutated. No solver/postprocessing launch, fitting, tuning, model
selection, or scientific admission change was performed.
