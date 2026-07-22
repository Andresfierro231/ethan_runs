---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/decision_summary.json
tags: [overnight, cfd-postprocess, thermal-closure, pressure-momentum, sign-convention]
related:
  - .agent/journal/2026-07-13/overnight-cfd-postprocess-prep.md
  - operational_notes/07-26/13/2026-07-13_OVERNIGHT_CFD_POSTPROCESS_PREP.md
task: AGENT-305
date: 2026-07-13
role: Coordinator/Implementer/Tester/Writer
type: work-product
status: active
---
# Overnight CFD Postprocess Prep

Purpose: prepare overnight-safe CFD postprocessing that advances closure and
predictive-model readiness without mutating native solver outputs or admitting
new thermal closure targets.

## Staged Job

- `scripts/run_salt2_coarse_thermal_repair_smoke.sbatch`

This job runs Salt2 coarse reconstructed-`T` repair smoke into:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/`

The job is intended to close the missing coarse thermal triplet input for the
thermal mesh gate. It does not admit HTC/UA/Nu to closure fitting.

## Already Built

- `work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/`

The sign/enthalpy review is diagnostic-only and reports `fit_admissible_count=0`.

## Postprocess Triage

Momentum-pressure:

- Salt2 pressure/momentum mesh-family evidence already exists in
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`.
- No new Salt2 pressure extraction should be launched tonight unless a new CFD
  run reaches terminal state and has an assigned harvest task.

Thermal:

- Salt2 medium and fine repaired thermal extraction exist.
- Salt2 coarse thermal extraction is the overnight-safe missing postprocess.
- Sign/enthalpy review remains blocking after existing evidence.

Live/terminal harvest:

- Corrected-Q job `3293924` should be harvested only after terminal state.
- Any older live jobs should be identified and documented before interpretation.

## Tomorrow Pickup

1. Check Slurm terminal state for any AGENT-305 job.
2. Validate `summary.json`, `outputs/reconstruction_trials.csv`, and coarse
   segment thermal CSV if present.
3. Rebuild the thermal mesh gate with coarse/medium/fine thermal rows.
4. Keep all thermal rows diagnostic until sign, enthalpy, downcomer, Nu, and GCI
   gates pass.
