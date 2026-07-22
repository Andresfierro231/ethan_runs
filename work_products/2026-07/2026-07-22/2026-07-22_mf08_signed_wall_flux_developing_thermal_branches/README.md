---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
  generated_at_utc: 2026-07-22T14:05:57.924311+00:00
task: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
tags:
  - MF08
  - signed-wall-flux
  - thermal-development
related:
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/summary.json
---

# MF08 Signed Wall-Flux Developing Thermal Branches

## Decision

Decision: `needs_source_basis_sign_aware_development_promising_diagnostic_only`.

The useful finding is sign-aware but still fail-closed. Setup-known branch heat
exchange gives the right physical signs: cooler/HX and passive-loss branches
cool the fluid, while heater and test-section branches heat the fluid. That is
enough to define candidate model forms and direction-of-effect, but not enough
to run or admit them.

All four required variants are labeled `needs_source_basis`. The package also
records the forbidden shortcut `forbidden_realized_wallHeatFlux_fit`.

## Scientific Use

Use this result to write that signed wall/source heat exchange is a plausible
missing-physics axis for TP/TW residuals, supported by D2/D3/D4 diagnostic
evidence and setup-side sign envelopes. Do not cite it as a released
coefficient, Fluid source/property release, wallHeatFlux runtime feature,
ordinary upcomer closure, pressure K evidence, or final score.

## Guardrails

No Fluid solve, scheduler action, solver/postprocessing/sampler/harvest/UQ
launch, native-output mutation, registry/admission mutation, Fluid/external
edit, fitting/model selection, validation/holdout/external scoring,
source/property release, coefficient admission, final score, realized
wallHeatFlux runtime input, or residual absorption into internal Nu was
performed.
