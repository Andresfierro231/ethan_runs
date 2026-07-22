---
provenance:
  - tools/analyze/build_s13_upcomer_exchange_average_field_thermal_reduction.py
  - tools/analyze/test_s13_upcomer_exchange_average_field_thermal_reduction.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/diagnostic_average_exchange_metrics.csv
tags: [status, s13, upcomer-exchange, diagnostic-average, thermal-reduction]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-average-field-thermal-reduction.md
  - imports/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/README.md
task: TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21

## Objective

Compute diagnostic average field and thermal reductions for the released seeded
upcomer-exchange control volume from existing whole-mesh cell VTK fields and
seed/core interface face topology. Keep all outputs nonadmissible and fail
closed for sampler, harvest, UQ, and coefficient use.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/`.

Salt2/Salt3/Salt4 each have a diagnostic row for seeded CV volume,
volume-weighted `U/T/rho`, interface area-weighted adjacent-core `U/T/rho`, a
signed outward exchange mass-flux proxy from OpenFOAM face area vectors, source
and sink thermal support, `tau_recirc_proxy`, and
`hA_source_side_proxy_W_K`.

Observed headline rows:

- Salt2: `V_recirc=1.19084663056e-05 m3`, `T_seed=443.184540921 K`,
  `mdot_positive_outward_proxy=2.68592194714e-05 kg/s`,
  `tau_recirc_proxy=868.807159089 s`, `hA_source_side_proxy=1136.13805588 W/K`.
- Salt3: `V_recirc=1.19084663056e-05 m3`, `T_seed=455.462760824 K`,
  `mdot_positive_outward_proxy=4.23665968058e-05 kg/s`,
  `tau_recirc_proxy=547.838912867 s`, `hA_source_side_proxy=1159.20788451 W/K`.
- Salt4: `V_recirc=1.19084663056e-05 m3`, `T_seed=469.904568133 K`,
  `mdot_positive_outward_proxy=7.65896288069e-05 kg/s`,
  `tau_recirc_proxy=301.390653047 s`, `hA_source_side_proxy=1191.40706792 W/K`.

The decision remains
`diagnostic_average_proxy_complete_sampler_harvest_blocked`: sampler-ready rows
`0`, admission-ready rows `0`, same-QOI UQ released `false`, and
S11/S12/S13/S15/S6 trigger `false`.

## Changes Made

- Added `tools/analyze/build_s13_upcomer_exchange_average_field_thermal_reduction.py`.
- Added `tools/analyze/test_s13_upcomer_exchange_average_field_thermal_reduction.py`.
- Generated:
  `diagnostic_average_exchange_metrics.csv`,
  `average_field_reduction.csv`,
  `interface_proxy_reduction.csv`,
  `thermal_proxy_reduction.csv`,
  `missing_gate_matrix.csv`,
  `downstream_gate.csv`,
  `no_mutation_guardrails.csv`,
  `source_manifest.csv`,
  `summary.json`, and `README.md`.
- Added this status file, journal entry, and import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_s13_upcomer_exchange_average_field_thermal_reduction.py tools/analyze/test_s13_upcomer_exchange_average_field_thermal_reduction.py`:
  passed.
- `python3.11 -m unittest tools.analyze.test_s13_upcomer_exchange_average_field_thermal_reduction`:
  passed, `5` tests.
- `python3.11 tools/analyze/build_s13_upcomer_exchange_average_field_thermal_reduction.py`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21`:
  passed.
- `python3.11 tools/docs/build_repo_index.py --check`:
  passed, `blocker register OK (15 entries)`.

## Unresolved Blockers

Pressure residual, viscosity basis, wallHeatFlux/`Q_wall_W`, `cp_J_kg_K`,
same-QOI UQ, production sampler harvest, and coefficient admission remain
blocked. The current package is useful diagnostic support only.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
OpenFOAM solver/postprocessing launch, surface extraction, field sampling,
sampler/harvest launch, Fluid/external edit, validation/holdout/external-test
scoring, fitting/model selection, source/property release, coefficient
admission, S11/S12/S13/S15/S6 trigger, blocker-register change, generated-index
refresh, or residual absorption into internal `Nu`.
