---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/refreshed_terminal_steady_state_gate.csv
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_bc_source_material_contract.csv
tags: [journal, agent-422, salt2, val-salt2, heat-loss-ledger, external-test]
related:
  - .agent/status/2026-07-15_AGENT-422.md
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/README.md
task: AGENT-422
date: 2026-07-15
role: cfd-pp/Thermal-admission/Implementer/Tester/Writer
type: journal
status: complete
---
# val_salt_test_2_coarse_mesh Postprocessing Admission Unlock

## Why

The coordinator questioned why `val_salt_test_2_coarse_mesh` remained blocked
when the case appeared fully converged. AGENT-417 had left it blocked only
because a matching section heat-loss ledger/admission package was missing, not
because the terminal CFD evidence was known to be unusable.

## What Changed

Built a reusable AGENT-422 package from existing postprocessing evidence:

- streamed the existing registry `wall_heat_flux_grouped.csv`;
- checked the final 300 s terminal window from 8302 to 8602 s;
- read terminal mdot monitor tails from the staged continuation
  `postProcessing/mdot_pipeleg_*/5182/surfaceFieldValue.dat` files;
- promoted section heat-loss terms into `val_salt2_section_heat_loss_ledger.csv`;
- attached the existing BC/source/material documentation from AGENT-354;
- wrote an explicit split/admission refresh.

## Results

`val_salt_test_2_coarse_mesh` is steady by the refreshed terminal-window gate:

- latest time: 8602 s;
- latest `total_Q_postProc`: 0.193062 W;
- maximum heat linear drift over the final 300 s: 0.0132872 W;
- maximum mdot relative linear drift: 7.9509e-05.

The older `hydraulic_stationary_heat_drifting` label is superseded for this
admission pass. The likely reason for the earlier flag is a ratio-style drift
detector reacting to very low-noise monotonic heat traces; the absolute drift is
sub-watt and small relative to the heat budget.

## Admission

New decision:

- `refreshed_steady_state_label`: `steady`
- `split_role`: `external_test_or_validation_candidate`
- `admission_decision`: `external_test_validation_candidate_unlocked`
- `usable_now`: `yes_external_test_validation`

Guardrail: if used as a blind external test, do not fit or tune on this row.
Realized CFD `wallHeatFlux` is diagnostic/scoring evidence, not a predictive
runtime input.

## Validation

Commands passed:

- `python3.11 -m py_compile tools/analyze/build_val_salt2_postprocessing_admission_unlock.py tools/analyze/test_val_salt2_postprocessing_admission_unlock.py`
- `python3.11 -m unittest tools.analyze.test_val_salt2_postprocessing_admission_unlock`

No native CFD outputs, registry state, scheduler state, generated indexes, or
external Fluid files were mutated.
