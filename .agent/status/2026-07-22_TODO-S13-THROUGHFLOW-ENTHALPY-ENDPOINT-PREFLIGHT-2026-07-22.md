---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/residual_readiness_gate.csv
tags: [status, s13, throughflow, enthalpy, open-cv, fail-closed]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/README.md
  - .agent/journal/2026-07-22/s13-throughflow-enthalpy-endpoint-preflight.md
  - imports/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight.json
task: TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22

## Objective

Define the same-window throughflow enthalpy endpoint prerequisites for the S13
residual-complete open-CV contract, inspect existing evidence, and emit exact
next commands/contracts without launching sampler/OpenFOAM or computing
residual values.

## Outcome

Decision:
`s13_throughflow_endpoint_preflight_complete_fail_closed_no_residual_value`.

The composite upcomer throughflow endpoint contract is now explicit for
Salt2/Salt3/Salt4: inlet `left_lower_leg:s00`, outlet `left_upper_leg:s04`,
positive along nominal main throughflow from lower-left upcomer inlet to
upper-left outlet. Historical coarse endpoint temperature rows exist for all
three cases, but they are diagnostic-only and include high inlet recirculation
ratios (`0.850529..0.895929`).

No same-basis residual value can be computed: `0/3` cases are harvest-ready,
`0/27` required case/input rows are release-or-harvest ready, and `0` residual
values were released.

## Changes Made

- Added reproducible builder:
  `tools/analyze/build_s13_throughflow_enthalpy_endpoint_preflight.py`.
- Added tests:
  `tools/analyze/test_s13_throughflow_enthalpy_endpoint_preflight.py`.
- Published work product:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/`.
- Published endpoint contract, required-input matrix, evidence disposition,
  postProcessing diagnostic support summary, staged sampling command contract,
  residual readiness gates, methodology, guardrails, source manifest, and
  summary.

## Validation

- `python3.11 tools/analyze/build_s13_throughflow_enthalpy_endpoint_preflight.py`: passed.
- `python3.11 -m py_compile tools/analyze/build_s13_throughflow_enthalpy_endpoint_preflight.py tools/analyze/test_s13_throughflow_enthalpy_endpoint_preflight.py`: passed.
- `python3.11 -m pytest tools/analyze/test_s13_throughflow_enthalpy_endpoint_preflight.py`: `6 passed`.

## Remaining Blockers

- Same-window endpoint face masks and normal/sign convention are not released
  for the S13 residual row.
- `T_in_bulk_K`, `T_out_bulk_K`, and true `mdot_throughflow_kg_s` endpoint
  integrals are missing for the same CV/window.
- Row-specific `cp_J_kg_K` release remains false.
- Storage and named non-wall loss/source-owner lanes are missing.
- Existing medium/fine exact S13 rows cover `Q_wall_W`, exchange mdot proxy,
  `tau_recirc_proxy_s`, and wall/core contrast, not `H_throughflow_net_W`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, source/property or Qwall release, residual value release, coefficient
fitting/admission, validation/holdout/external-test scoring, candidate freeze,
final-score claim, S11/S12/S13/S15/S6 trigger, hidden multiplier, residual
absorption into internal Nu, endpoint proxy substitution, or runtime-leakage
relaxation occurred.
