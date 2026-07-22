---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/bulk_integral_heat_partition_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/bulk_integral_model_form_ladder.csv
tags: [status, s13, predictive-1d, heat-partition, bulk-integral, no-fit]
related:
  - .agent/journal/2026-07-22/s13-bulk-integral-heat-partition-feasibility.md
  - imports/2026-07-22_s13_bulk_integral_heat_partition_feasibility.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/README.md
task: TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22

## Objective

Take the cleanest current path toward a predictive 1D model by testing a
no-fit bulk-integral heat partition before exchange-cell coefficient fitting.
Use averaged states only as future model drivers while preserving `Q_wall_W`,
source-side heat flow, exchange enthalpy scale, and energy residual as integral
outputs.

## Outcome

Complete. Decision:
`bulk_integral_heat_partition_feasible_diagnostic_no_fit_residual_next`.

The leading modeling direction is:

`Q_wall_model = F_wall * Q_source_side_net_static_bc_W`, with the remaining heat
kept as an explicit residual/throughflow/storage lane.

Observed diagnostic partition:

- Salt2: `F_wall = 0.13896146612096516`
- Salt3: `F_wall = 0.13795514599531333`
- Salt4: `F_wall = 0.13693697990467257`
- Mean: `0.13795119734031702`
- Range: `0.002024486216292587`

This is stable enough to advance as a no-fit diagnostic model direction. It is
not a fitted coefficient and is not admitted for predictive release.

The same-basis energy residual is still not computable because cp/property
release and same-window throughflow enthalpy endpoints remain blocked. Exchange
cell coefficients remain deferred because `mdot_exchange`, `tau_recirc`, and
wall/core contrast have large medium/fine spread.

## Changes Made

- Added reusable builder:
  `tools/analyze/build_s13_bulk_integral_heat_partition_feasibility.py`.
- Added tests:
  `tools/analyze/test_s13_bulk_integral_heat_partition_feasibility.py`.
- Generated package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/`.
- Generated:
  `bulk_integral_heat_partition_rows.csv`,
  `partition_stability_summary.csv`,
  `energy_residual_feasibility.csv`,
  `bulk_integral_model_form_ladder.csv`,
  `progression_gate.csv`,
  `source_manifest.csv`,
  `summary.json`, and `README.md`.
- Updated own board row, this status, matching journal, and import manifest.

## Validation

- `python3.11 -m pytest tools/analyze/test_s13_bulk_integral_heat_partition_feasibility.py`:
  passed, `7` tests.
- `python3.11 -m py_compile tools/analyze/build_s13_bulk_integral_heat_partition_feasibility.py tools/analyze/test_s13_bulk_integral_heat_partition_feasibility.py`:
  passed.
- `python3.11 tools/analyze/build_s13_bulk_integral_heat_partition_feasibility.py`:
  passed and regenerated the package outputs.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Scheduler action: `false`.
- Solver/postProcess/sampler/harvest/UQ launched: `false`.
- Generated docs index refreshed: `false`; another active row owns generated index paths.
- Source/property or Qwall release: `false`.
- Coefficient fitting/admission: `false`.
- Production harvest/admission: `false`.
- Validation/holdout/external-test scoring: `false`.
- Candidate freeze/final score/S11/S12/S13/S15/S6 trigger: `false`.
- Residual absorbed into internal Nu: `false`.

## Next Useful Action

Build the residual-complete open-CV energy balance contract: same-window
throughflow enthalpy endpoints, row-specific cp/property provenance, storage
policy, and named residual terms. That is the next step toward a predictive 1D
model; exchange-cell coefficients should wait until the bulk residual demands
them and mesh/source-property gates clear.
