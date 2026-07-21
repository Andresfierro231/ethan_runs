# Water Postprocess And Closure Table

Date: `2026-07-04`
Task: `AGENT-177`
Role: Coordinator / Implementer / Writer

## Actions

- Submitted dependent Water postprocess job `3275363` through `login3`:
  - script: `tmp/2026-07-04_water_postprocess_job/run_water_postprocess_after_3265970.sbatch`
  - dependency: `afterany:3265970`
  - partition: `development`
  - purpose: rerun the postprocessing run-status inventory after Water job
    `3265970` exits, then refresh the consolidated closure/model package.
- Submitted immediate lightweight next-1D-model job `3275364` through `login3`:
  - script: `tmp/2026-07-04_next_1d_model_job/run_next_1d_model_forms.sbatch`
  - partition: `development`
  - purpose: regenerate the consolidated closure table and next model-form
    screen under Slurm.
- Added `tools/analyze/build_consolidated_closure_table.py`.
- Added `tools/analyze/build_next_1d_model_forms.py`.
- Generated `work_products/2026-07-04_consolidated_closure_and_model_jobs/`.

## Salt Perturbation Diagnosis

The Salt perturbation runs are not valid closure-training points in their
current form. The monitors are flat, but the operating point did not move from
the nominal parent state after the Q change. The July 1 T3 gate records the
expected laminar natural-circulation response as roughly `mdot ~ Q^(1/3)`.
For ±5-10% heater-power changes, the expected mdot movement is about
`1.6-3.5%`; the observed movement was generally below `0.3%`, often with the
wrong sign. That is false-steady behavior: numerically quiet near the old fixed
point, not re-equilibrated to the new boundary condition.

They are not useless: they document an important failure mode and remain useful
for workflow hardening. They are not admissible as Re/Q variation for fitting
friction, bend-K, recirculation, or thermal closure terms.

To make this family useful, restart or rerun the perturbations with:

- enough runtime for several thermal relaxation times past the perturbation
  restart;
- a convergence gate that requires both operating-point movement and
  re-plateauing;
- a Q/insulation mutation audit before submission, because previous
  `hiins`/`loins` cases did not actually change the live insulation knob;
- final admission only for rows whose operating-point gate reports
  `requalified`.

## Current Consolidated Package

`consolidated_closure_table.csv` currently has `78` rows across `14` nominal or
run-status labels. It joins:

- July 1 mesh-corrected segment friction rows;
- June 30 thermal HTC/UA' rows;
- June 30 upcomer/downcomer recirculation rows;
- July 1 segment pressure-drop/model-comparison rows;
- July 4 run-status rows for recent packed jobs.

Important handling: Salt perturbation run-status rows are represented as
separate `case_status` rows. They are deliberately not joined onto nominal Salt
closure rows, because the staged perturbation case directories share final
folder names with nominal cases.

## 1D Model Screen

The immediate local run shows:

- prior `global_mean_mult`: mean absolute mdot error `3.662%`;
- prior `per_leg_friction`: mean absolute mdot error `9.941%`;
- per-leg f(Re) screen has four span/method groups with three positive nominal
  Salt points each, but these remain screen-only because the perturbation rows
  are false-steady and excluded.

## Queue State At Submission

- `3265970` Water continuation: running.
- `3275363` Water postprocess: pending on dependency.
- `3275364` next 1D model forms: pending on development resources.
