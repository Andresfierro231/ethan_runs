---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensor_delta.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/owner_delta.csv
tags: [journal, forward-model, phase-h, heat-loss-sensitivity]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21.md
  - imports/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/README.md
task: TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Phase H Compute-Safe Sensitivity

## Attempted

Claimed the Phase H compute-safe sensitivity row and built a self-contained
work-product package under
`work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/`.

The runner loads Phase E train role rows and F-J residual baselines, applies the
six predeclared one-at-a-time perturbations, invokes local Fluid `solve_case`
inside subprocess workers, and flushes the four requested CSVs after every row.

## Observed

All six workers completed with `root_status=accepted` inside the `90 s`
timeout. No fail or timeout rows occurred.

The TW5/heated-incline response was:

- `lower_leg_hA_scale_0.5`: improves by `4.59310690807564 K` in absolute residual.
- `lower_leg_hA_scale_2.0`: worsens by `7.478576361192836 K`.
- `global_passive_hA_scale_0.5`: improves by `51.63369382647278 K`.
- `global_passive_hA_scale_2.0`: worsens by `27.638341480119664 K`.
- `ambient_drive_delta_+15K`: improves by `13.472549886792422 K`.
- `ambient_drive_delta_-5K`: worsens by `4.492058432100237 K`.

The global passive hA decrease also improved all-probe MAE by
`47.133590749185956 K`; the global passive hA increase worsened all-probe MAE
by `28.155039906096434 K`.

## Inferred

The Phase E thermal residual is responsive to passive heat-loss assumptions.
The lower-leg-only lane is not sufficient to explain the dominant TW5 residual
on its own, while global passive heat-loss scaling has a large effect. This
points toward broad external-wall-network/source-family coverage, sign/unit
basis, missing source/sink physics, axial redistribution, wall/test-section
coupling, or recirculation/stratification as higher-value follow-up lanes than
immediate model-form tuning.

The result is still diagnostic only. It does not justify selecting
`global_passive_hA_scale_0.5` as a repair, because that would be fitting/model
selection against train residuals without a predeclared physical basis.

## Contradictions Or Caveats

The first subprocess implementation used `subprocess.run(..., timeout=150,
capture_output=True)` and was interrupted after worker communication failed to
return promptly. The final implementation uses process-group isolation and
manual polling, so timeout behavior is now explicit and partial CSV flushing is
preserved.

The baseline comparison uses Phase E/F-J train diagnostic references only.
Validation, holdout, and external-test rows were not loaded for scoring or
model selection.

## Next Useful Actions

1. Audit which source families dominate the global passive hA effect and
   whether any row has a sign, unit, area, or segment-mapping defect.
2. Compare passive heat-loss response against recovered setup-known
   source/sink rows, but keep source/sink runtime admission blocked until an
   explicit source-model API and source/property gate exist.
3. Run one predeclared physical-basis repair only after the dictionary or heat
   path evidence identifies a specific admissible defect.
4. Preserve the train/validation/holdout/external-test separation until a
   frozen candidate exists.
