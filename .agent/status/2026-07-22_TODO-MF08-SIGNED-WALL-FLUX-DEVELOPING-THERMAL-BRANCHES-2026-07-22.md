---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
  generated_at_utc: 2026-07-22T14:05:57.924311+00:00
task: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
tags:
  - status
  - MF08
  - signed-wall-flux
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches
---

# TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22

## Objective

Create sign-aware thermal-development model-form candidates for cooler/passive
cooling and heater/test-section heating branches without using realized
wallHeatFlux, fitting, or source/property release.

## Outcome

Decision: `needs_source_basis_sign_aware_development_promising_diagnostic_only`. Required variants: `4`.
Train-smoke-ready variants: `0`.
Required variants needing source basis: `4`.
Forbidden wallHeatFlux-fit shortcuts: `1`.

## Changes Made

- Wrote runtime-legal source table.
- Wrote setup/source-envelope provenance table.
- Wrote signed branch flux magnitude envelope.
- Wrote reset/Graetz basis table.
- Wrote assumptions/caveats and expected TP/TW/pressure direction-of-effect.
- Wrote candidate gate, guardrails, README, summary, status, journal, and import manifest.

## Validation

pending

## Guardrails

- Fluid solve: false.
- Scheduler action or solver/postprocessing/sampler/harvest/UQ launch: false.
- Native-output mutation: false.
- Registry/admission mutation: false.
- Fluid/external edit: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Realized wallHeatFlux runtime input: false.
- Source/property release, coefficient admission, final score: false.
- Residual-internal-Nu absorption: false.
