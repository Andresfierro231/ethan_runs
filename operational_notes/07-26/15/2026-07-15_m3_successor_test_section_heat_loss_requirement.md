---
provenance:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/README.md
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
tags: [forward-predictive-model, m3, test-section, heat-loss, admission, thesis]
related:
  - operational_notes/maps/forward-predictive-model.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/README.md
task: AGENT-430
date: 2026-07-15
role: Coordinator/Writer
type: operational_note
status: complete
---
# M3 Successor Test-Section Heat-Loss Requirement

## User Decision

Do not interpret M3 as "remove the test section." The current M3 diagnostic
mode removed the CFD test-section net term only as an ablation. The next
M3-like predictive model must include the test section through an explicit
setup-only heat-loss model.

Use the working name `M3+TS` until a later admission package chooses a final
name.

## Current Evidence

AGENT-424 reports:

- M2 (`CFD heater + test-section net + cooler`, pressure-root mdot):
  `10.397%` mean mdot error and `26.972 K` all-probe RMSE.
- M3 (`CFD heater + cooler only`, pressure-root mdot):
  `16.826%` mean mdot error and `18.023 K` all-probe RMSE.

Interpretation: the current CFD test-section compatibility term helps mdot but
hurts TP/TW RMSE. That is model-form evidence that the compatibility
representation is not final. It is not evidence that test-section heat loss is
zero or can be omitted.

## Predictive Target

The target form is:

```text
Find mdot such that:
  sum(dp_buoyancy(mdot, T) - dp_loss(mdot; f_D, K, rho, mu, geometry)) = 0

with thermal state from:
  Q_heater_model
  Q_cooler_HX_model
  Q_test_section_loss_model
  Q_passive_external_boundary_model
```

The new term should be first-class:

```text
Q_test_section_loss_model =
  sum_i [ h_i A_i coverage_i (T_drive_i - T_ambient_i) + Q_rad_i_optional ]
```

or the equivalent resistance-network form:

```text
Q_test_section_loss_model =
  sum_i [ (T_fluid_i - T_ambient_i) / R_total_i ]
```

where `R_total_i` may include internal convection, wall conduction, insulation,
external convection, and admitted radiation if that path is enabled without
double counting CFD `wallHeatFlux`.

## Allowed Inputs

Allowed at runtime:

- geometry and segment areas/lengths;
- setup h/Ta/Tsur/emissivity/coverage dictionaries;
- material properties and declared wall/layer parameters;
- heater electrical input and admitted heater model parameters;
- cooler/HX setup metadata and admitted cooler model parameters;
- solver-state temperatures for the chosen setup-only drive.

Not allowed at runtime:

- realized CFD test-section net heat;
- realized CFD `wallHeatFlux`;
- CFD mdot;
- imposed CFD cooler duty;
- validation or holdout TP/TW temperatures.

## Board TODO

The implementation row is `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`.

Acceptance should require:

- build and score `Q_test_section_loss_model` under train/validation/holdout
  split policy;
- compare `M3+TS` against M2 and diagnostic M3 on mdot plus TP/TW errors;
- preserve recirculation/internal-Nu guardrails;
- report blocked gates explicitly if the model is not admitted.

## Do Not Do

- Do not present diagnostic M3 as a final predictive model.
- Do not say the test section can be deleted.
- Do not fit a hidden global multiplier to held-out errors.
- Do not absorb boundary losses into internal Nu or single-stream upcomer
  coefficients in the current recirculating regime.
