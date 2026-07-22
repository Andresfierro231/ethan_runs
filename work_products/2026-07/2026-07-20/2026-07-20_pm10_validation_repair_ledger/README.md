---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission/pm10_upcomer_anchor_classification.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_3305547_failure_repair/partial_parse_inventory.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_3305547_failure_repair/remaining_case_relaunch_queue.csv
tags: [pm10, upcomer, validation, recirculation, repair-ledger]
related:
  - .agent/status/2026-07-20_AGENT-570.md
  - .agent/journal/2026-07-20/pm10-validation-repair-ledger.md
task: AGENT-570
date: 2026-07-20
role: cfd-pp/Upcomer-onset/Reviewer/Writer
type: work_product
status: complete
---
# PM10 Validation Repair Ledger

Decision: `pm10_validation_ready_recirc_diagnostic_no_relaunch`.

This package implements the PM10 side of the current progress plan. It
reconciles the older 3305547 failure-repair partial inventory with the later
PM10 upcomer-anchor classification package. It does not run postprocessing,
submit or relaunch jobs, mutate native CFD outputs, change registry/admission
state, fit, tune, select models, score, or change scientific admission.

## Result

The current PM10 validation rows are usable as recirculation diagnostics:

- `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q` each have
  three matched-plane rows in the later PM10 classification package.
- All four classify as `recirculation_diagnostic`.
- Reverse-flow metrics are large: reverse-area fraction about `0.77-0.79` and
  reverse-mass fraction about `0.500`.
- Richardson number remains high: about `118-248`.

Therefore PM10 validates strongly recirculating upcomer behavior at +/-10Q. It
does not unlock ordinary-pipe, onset-transition, F6, component-K, fitting,
model-selection, runtime-input, or final-scorecard use.

## Files

- `pm10_validation_use_ledger.csv`: row-level validation use and forbidden use.
- `pm10_parse_repair_decision.csv`: reconciliation of stale partial inventory
  against the later parsed classification.
- `pm10_next_use_contract.csv`: exact follow-on conditions for any future PM10
  use.
- `source_manifest.csv`: read-only inputs and generated artifacts.
- `summary.json`: machine-readable decision.

## Next Step

Use PM10 in narrative and diagnostic validation as evidence that +/-10Q rows
remain recirculating. Do not spend compute repairing PM10 for fit/admission
unless a future task needs inventory completeness beyond the four current
validation rows; even then, repair remains inventory-only with no fit or
model-selection release.
