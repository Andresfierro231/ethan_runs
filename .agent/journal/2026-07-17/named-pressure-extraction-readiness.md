---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger/target_package_gate_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/segment_pressure_model_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/corner_k_gate_matrix.csv
tags: [pressure-ledger, named-losses, f6, extraction-readiness]
related:
  - .agent/status/2026-07-17_AGENT-523.md
  - imports/2026-07-17_named_pressure_extraction_readiness.json
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/README.md
task: AGENT-523
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Named Pressure Extraction Readiness

Task: AGENT-523

## Attempted

Converted the pressure/named-loss evidence into an implementable extraction
readiness package. The package consumes the LitRev named-loss table, AGENT-521
gate contract, segment-pressure scorecard, F6 model-form ladder, and
`val_salt2` corner-K diagnosis to rank the next hydraulic work without changing
admission state.

## Observed

The audit reviewed 33 named pressure rows. None are fit-ready under current
gates. Three component/cluster rows and six branch/straight rows are extraction
targets after repair. Twenty-four rows remain diagnostic or section-effective
because recirculation or universal-name guardrails block ordinary coefficients.
All 33 rows need same-QOI mesh/time uncertainty before publication-grade
coefficient admission.

## Inferred

The fastest honest F6 progress is not another global friction fit. It is a
targeted pressure-extraction repair: centerline tap lengths, explicit
pressure/velocity bases, straight-loss subtraction, component isolation,
reverse-flow masks, and same-window uncertainty. Reset/development ideas from
the literature are still useful, but they need an explicit Fluid API contract
before they can be scored without hiding a multiplier.

## Contradictions And Caveats

This work does not resolve `f6-friction-re-correction`. It narrows the blocker:
current rows are useful as diagnostics and extraction design, but not as
ordinary `f_D`, `K`, or reset-development admissions. The package intentionally
keeps `F3_shah_apparent` as the production closure.

## Next Useful Actions

Start with `next_pressure_extraction_queue.csv`. The first implementable task is
`raw_two_tap_connector_and_component_repair`; it should produce centerline tap
lengths, final pressure/velocity bases, straight-loss subtraction, component
isolation, and UQ for the three component/cluster candidates. The second task
should finalize pressure and velocity basis fields for the broader branch and
straight-section rows.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, or active-agent scoped
artifacts were mutated. No solver/postprocessing launch, fitting, tuning, model
selection, or scientific admission change was performed.
