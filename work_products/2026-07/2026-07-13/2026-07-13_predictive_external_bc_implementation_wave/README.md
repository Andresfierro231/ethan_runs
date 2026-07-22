---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/hx_validation_guardrail_scorecard.csv
tags: [forward-model, predictive-1d, external-boundary, radiation, hydraulic-guardrail]
related:
  - .agent/status/2026-07-13_AGENT-297.md
  - .agent/journal/2026-07-13/predictive-external-bc-implementation-wave.md
task: AGENT-297
date: 2026-07-13
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive External BC Implementation Wave

Generated: `2026-07-13T22:12:15+00:00`  
Task: `AGENT-297`

This package implements the repo-local bridge for the next CFD-to-1D parity
phase. It does not mutate native CFD solver outputs and does not edit external
Fluid source in this sandbox.

## Outputs

- `cfd_external_boundary_dictionary.csv`: Fluid-ready segment/role external
  boundary rows from AGENT-263 plus wall-layer metadata.
- `boundary_mode_scorecard.csv`: E0/E1/E2 wall-layer residuals with validation
  split roles.
- `hx_validation_guardrail_scorecard.csv`: Salt2 train, Salt3 validation, Salt4
  holdout HX score rows with hydraulic guardrails.
- `hydraulic_guardrail_summary.csv`: mdot-bias summary by forward-v0 variant.
- `implementation_decision_table.csv`: decisions and next owners.
- `fluid_external_boundary_patch_plan.md`: exact downstream Fluid edit plan.

## Main Result

The external boundary dictionary is ready for Fluid API implementation, but the
current workspace keeps `../cfd-modeling-tools/**` read-only. Radiation policy is
fixed: setup-level external-boundary parity must include emissivity/Tsur
radiation; realized CFD `wallHeatFlux` replay must not add a separate radiation
term.

The validation split is now usable for one-scalar HX scoring, but hydraulic
guardrails still fail: forward-v0 Salt rows overpredict mdot, so thermal
improvements cannot be interpreted as end-to-end prediction yet.

HX package caveat: `fit_protocol_status.csv` and
`validation_split_requirements.csv` still contain stale missing-split language.
Use the later split-aware `hx_validation_splits.csv`, `hx_fit_parameters.csv`,
and `hx_primary_forward_scores.csv` artifacts for this scorecard.

## Row Counts

- external boundary rows: `24`
- boundary score rows: `24`
- HX score rows: `6`
- hydraulic summary rows: `2`
