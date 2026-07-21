# ROM Model-Form Fits and 1.4 in Boundary Run

Date: `2026-07-01`  
Task: `AGENT-170`  
Status: local Fluid-solver run complete; no OpenFOAM execution

## What Was Checked

Claude had already run a small AGENT-168 predictivity trial in
`work_products/2026-07-01_claude_1d_predictivity_trial/`. That trial includes
the planned casewise `cfd_closures_2026_07_01` hydraulic closure form, but it
fixes the scenario to `predictive_airside_ins_1.0in_rad_1`.

The missing item was the CFD boundary match: Salt Jin CFD rows use about
`1.40 in` outer insulation, while the scored readable bundle had only `1.0 in`
and `2.0 in` states. This package runs a local in-memory `1.4 in`, radiation-on
scenario and closure-term fit variants without editing the external Fluid repo.

## Generated Outputs

Work products: `work_products/2026-07-01_rom_model_form_fits_and_1p4_boundary`

- `model_form_fit_results.csv`: per-case model-form predictions.
- `model_form_summary.csv`: side-by-side performance over high-trust Salt 2-4.
- `closure_fit_parameters.csv`: fitted/global closure coefficients.
- `boundary_sensitivity.csv`: default-closure `1.0/1.4/2.0` and rad-off sweep.
- `claude_trial_audit.csv`: what AGENT-168 had already produced.
- `figures/*.png`: side-by-side model-performance plots.

## Current Best Local Result

Best local Salt 2-4 mean absolute mdot error: `3.103%`
from `fit_major_k90_1p4`.

The `1.4 in` default boundary run is now present. It should be used as the
matched-boundary baseline instead of treating the older `1.0 in`/`2.0 in`
bundle as final.

## Compute and Storage

- Current Slurm usage observed before this run: `4 NuclearEnergy production jobs plus 1 NuclearEnergy-dev idev job observed earlier via squeue`.
- This local run used a worker-parallel Python coupled-solver process set on the
  active `NuclearEnergy-dev` node, no OpenFOAM, and wrote less than
  `1 MB`.
- Runtime class: `64-worker local Python coupled-solver evaluation; grid_level=compact on the active dev node`.

## Limitations

- These are local direct solver evaluations, not a committed external Fluid
  campaign. The external Fluid repo remains read-only from this task.
- The two-parameter closure fit uses only Salt 2-4 high-trust CFD mdot targets,
  so it is useful for model-form comparison but is not a robust predictive
  correlation by itself.
- Pressure distribution, segment temperatures, and experimental validation still
  need separate scoring before any fitted model is paper-ready.
