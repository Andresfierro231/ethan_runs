# AGENT-170 ROM Model-Form Fits and 1.4 in Boundary Run

Date: `2026-07-01`  
Role: Coordinator / Implementer / Writer  
Status: selected local coupled-solver run complete

## Observed

- Claude AGENT-168 had already produced `work_products/2026-07-01_claude_1d_predictivity_trial/predictivity_mdot_table.{csv,json}`.
- That trial includes `model_default`, `zero_minor`, `zero_major_zero_minor`, and `cfd_closures_2026_07_01`, but its scenario is fixed to `predictive_airside_ins_1.0in_rad_1`.
- The Claude trial did not include the CFD-matched `1.4 in` Salt Jin boundary.
- Current Slurm usage observed before this work:
  - four running NuclearEnergy production jobs: `3265969`, `3265970`, `3265971`, `3265972`
  - one running NuclearEnergy-dev allocation: `3269598` on `c318-008`
- The active shell is on `c318-008` inside job `3269598`; `sbatch` refused from this node with "sbatch not available on compute nodes".
- Scratch space is not the blocker: `/scratch` had about `2.9P` available; outputs from this run are under `1 MB`.

## Implemented

- Added `tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py`.
- Added tests in `tools/analyze/test_rom_model_form_fits_and_1p4_boundary.py`.
- Added a launch template at `tmp/2026-07-01_rom_model_form_jobs/run_compact_model_form_fits.slurm`; because this shell is already on an idev compute node, the actual run was launched directly with `python3 ... --grid-level selected --workers 32`.
- The runner imports the external Fluid solver read-only from `../cfd-modeling-tools/tamu_first_order_model/Fluid` and writes all outputs inside `ethan_runs`.
- The runner constructs an in-memory `ScenarioConfig` for `1.4 in`, radiation on, without editing the external Fluid scenario YAML.
- The selected run evaluates:
  - default closures at `1.0`, `1.4`, and `2.0 in`, radiation on
  - default closures at `1.4 in`, radiation off
  - zero-minor ablation at `1.4 in`
  - Claude casewise CFD closure terms at `1.4 in`
  - three endpoint-surrogate fitted forms seeded from Claude's `1.0 in` default-to-CFD-closure endpoints

## Verification

- `python3 -m pytest tools/analyze/test_rom_model_form_fits_and_1p4_boundary.py -q`
  - result: `5 passed`
- `python3 -m py_compile tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py`
  - result: passed
- `python3 tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py --grid-level selected --workers 32`
  - result: completed twice; final package timestamp `2026-07-01T16:58:39-05:00`

## Outputs

- Report package: `reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary/`
- Work products: `work_products/2026-07-01_rom_model_form_fits_and_1p4_boundary/`
- Import manifest: `imports/2026-07-01_rom_model_form_fits_and_1p4_boundary.json`
- Key tables:
  - `model_form_summary.csv`
  - `model_form_fit_results.csv`
  - `closure_fit_parameters.csv`
  - `boundary_sensitivity.csv`
  - `claude_trial_audit.csv`
- Figures:
  - `figures/model_form_mdot_error_bar.png`
  - `figures/predicted_vs_cfd_mdot.png`
  - `figures/boundary_sensitivity_mdot_error.png`

## Results

- Best selected form over high-trust Salt 2-4 mdot targets:
  - `surrogate_fit_major_k90_1p4`
  - mean absolute mdot error: `3.653%`
  - RMSE mdot error: `5.486%`
  - coefficients: `major_loss_multiplier=1.5843483899448736`, `k90=6.913787991793965`, `k20=0.0`, total fixed K `27.65515196717586`
- Matched-boundary default result:
  - `boundary_default_1p4_rad_on`
  - mean absolute mdot error: `35.393%`
  - this is worse than the old `1.0 in` default mean error of `27.367%`
- Claude casewise CFD closures replayed at `1.4 in`:
  - `cfd_casewise_closures_1p4_rad_on`
  - mean absolute mdot error: `13.915%`
  - better than default but over-resistive for Salt 2-4 relative to the endpoint-surrogate two-term blend
- Zero-minor ablation at `1.4 in` remains poor:
  - mean absolute mdot error: `44.511%`

## Interpretation

- The missing `1.4 in` boundary scenario is now represented in the local coupled 1D comparison package.
- Boundary matching alone does not fix the 1D model. Increasing the insulation from `1.0 in` to `1.4 in` increases predicted mdot for the default hydraulic model and worsens the mdot bias.
- The useful signal is hydraulic closure form: a moderate two-term major-plus-bend-K fit performs much better than either default losses or full casewise CFD closures.
- The endpoint-surrogate fit is credible as a meeting-ready diagnostic, not as a final paper-ready closure. It is seeded from Claude's `1.0 in` endpoint behavior and evaluated at `1.4 in`, not independently optimized by dense grid at `1.4 in`.

## Limitations

- Energy-error columns are `nan` for Salt 2-4 Jin because the available local representative heat-balance table currently carries only Kirst rows. The package still reports qhx/qambient predictions and TP/TW RMSE, but the Jin heat-balance denominator must be added before claiming full energy performance.
- Several rows have `accepted_for_validation=False` because the upstream Fluid solver marks high-temperature validity/root status conservatively. The mdot roots are still reported, but validation status must be treated explicitly in paper-facing comparisons.
- Dense closure-grid fitting was not run. A measured selected run of 39 coupled solves took minutes with 32 workers; a compact dense fit is approximately `~450` coupled solves and a full dense fit is approximately `~4700` coupled solves. Plan on one node, 32-64 workers, roughly `1-2 h` for compact and `6-10 h` for full after refactoring candidate scoring to per-solve parallelism.

## Next Actions

- Add Jin heat-balance reference rows to the local validation/bakeoff package so `mean_energy_error_pct_of_heater` is populated for Salt 2-4 Jin.
- Refactor dense-grid candidate scoring so each salt/candidate solve is a separate parallel task, then submit the compact or full dense fit on a fresh allocation.
- Decide whether the endpoint-surrogate major-plus-K form should be promoted into the external Fluid scenario/config layer, or kept as an `ethan_runs` comparison artifact until experimental validation exists.
- Compare the fitted hydraulic closure against pressure-distribution and segment-resistance targets, not mdot alone.

## Detailed Run Ledger Requested By User

This section was added after the user asked for a more explicit record of what
was run, assumptions, provenance, and next steps before continuing dense model
fits.

### Commands and Runs

- `squeue -u $USER`
  - Purpose: current compute inventory.
  - Important result: four production CFD jobs were running on `NuclearEnergy`
    and one `NuclearEnergy-dev` allocation `3269598` was running on `c318-008`.
- `df -h . /scratch /tmp`
  - Purpose: storage check before generating reports.
  - Important result: `/scratch` had about `2.9P` available; storage is not a
    blocker for 1D model comparison artifacts.
- `head -20 work_products/2026-07-01_claude_1d_predictivity_trial/predictivity_mdot_table.csv`
  - Purpose: determine whether Claude already ran the requested closure cases.
  - Important result: Claude ran default, zero-minor, zero-major/zero-minor,
    and `cfd_closures_2026_07_01`, but only at the `1.0 in` rad-on scenario.
- `python3 -m pytest tools/analyze/test_rom_model_form_fits_and_1p4_boundary.py -q`
  - Purpose: lock helper logic for error metrics, scenario construction, loss
    definitions, and ranking.
  - Result: `5 passed`.
- `python3 -m py_compile tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py`
  - Purpose: syntax check after runner edits.
  - Result: passed.
- Interrupted serial/early smoke attempts:
  - `python3 tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py --quick`
  - `python3 -c "... solver.solve_case(...)"` benchmark
  - `python3 tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py --quick --workers 8 ...`
  - Reason: these demonstrated that each coupled Fluid `solve_case` is expensive
    in the current environment and that dense fitting should be treated as a
    node job, not a login-side throwaway.
- Completed selected run:
  - `python3 tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py --grid-level selected --workers 32`
  - Purpose: run the missing `1.4 in` boundary comparison and selected closure
    forms using the full coupled 1D solver.
  - Result: completed, produced 39 detail rows, 10 summary rows, 3 figures.

### Cases That Matter

- Training / high-trust comparison cases for mdot:
  - `Salt 2 Jin`: CFD mdot target `0.01318354663 kg/s`
  - `Salt 3 Jin`: CFD mdot target `0.01496689828 kg/s`
  - `Salt 4 Jin`: CFD mdot target `0.01698467657 kg/s`
- Low-trust context row:
  - `Salt 1 Jin`: CFD mdot target `0.01126494445094736 kg/s`, flagged
    `low_early_window`; useful for display/context only, not fit scoring.
- Claude prior run:
  - artifact: `work_products/2026-07-01_claude_1d_predictivity_trial/predictivity_mdot_table.json`
  - scenario: `predictive_airside_ins_1.0in_rad_1`
  - row count: `15`
  - contains `cfd_closures_2026_07_01`: yes
  - contains `1.4 in` boundary: no

### Model Forms Evaluated In Selected Run

- Boundary sweeps with default loss coefficients:
  - `boundary_default_1p0_rad_on`
  - `boundary_default_1p4_rad_on`
  - `boundary_default_2p0_rad_on`
  - `boundary_default_1p4_rad_off`
- Explicit closure/model forms at `1.4 in`, rad-on:
  - `default_1p4_rad_on`
  - `zero_minor_1p4_rad_on`
  - `surrogate_fit_major_defaultK_1p4`
  - `surrogate_fit_k90_major1_1p4`
  - `surrogate_fit_major_k90_1p4`
  - `cfd_casewise_closures_1p4_rad_on`

### Assumptions

- The 1D boundary intended to match Salt Jin CFD is `1.4 in` insulation with
  radiation enabled. This follows the CFD wall-model summaries saying Salt Jin
  rows use patchwise `rcExternalTemperature` layered walls with about `1.40 in`
  outer insulation.
- The external Fluid repository was used read-only. The task did not edit
  external Fluid scenario YAML, and the `1.4 in` scenario was constructed
  in-memory through `ScenarioConfig`.
- Fit scoring uses Salt 2-4 Jin continuation mdot targets only. Salt 1 remains
  a low-trust early-window context row.
- The selected fit is an endpoint-surrogate, not a dense optimum. It blends
  between default and Claude's CFD-closure endpoint behavior from the existing
  `1.0 in` trial, then evaluates those coefficients at `1.4 in`.

### Found So Far

- Boundary matching alone is not sufficient:
  - old default `1.0 in` rad-on mean absolute mdot error: `27.367%`
  - default `1.4 in` rad-on mean absolute mdot error: `35.393%`
- Claude casewise CFD closures improve the matched-boundary run but remain
  over-resistive:
  - `cfd_casewise_closures_1p4_rad_on`: `13.915%` mean absolute mdot error.
- The best selected diagnostic form is a moderate two-term global hydraulic
  closure:
  - `surrogate_fit_major_k90_1p4`: `3.653%` mean absolute mdot error.
  - coefficients: `major_loss_multiplier=1.5843483899448736`,
    `k90=6.913787991793965`, `k20=0.0`.

### Provenance

- External solver source:
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- Existing Claude closure trial:
  - `work_products/2026-07-01_claude_1d_predictivity_trial/`
- Local validation references:
  - `reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/`
- Local bakeoff references:
  - `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/`
- New AGENT-170 outputs:
  - `reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary/`
  - `work_products/2026-07-01_rom_model_form_fits_and_1p4_boundary/`
  - `imports/2026-07-01_rom_model_form_fits_and_1p4_boundary.json`

### Immediate Next Step

The next user-requested continuation is:

1. Populate Jin heat-balance reference rows using the July 1 validation
   `case_metric_summary.csv`, because it already contains Salt 2/3/4 Jin
   `cfd_removed_w`, `cfd_ambient_w`, `cfd_total_loss_w`, and `cfd_heater_w`.
2. Refactor dense fitting so each candidate/salt solve is an independent
   parallel task rather than a worker doing all three salts serially.
3. Run `--grid-level compact` at `1.4 in` on the current compute node.
4. Leave an explicit note to run `--grid-level full` later as a larger
   allocation job.

## Compact Dense Fit Follow-Up

After the detailed ledger above, the runner was updated and the compact dense
fit was executed on the active `NuclearEnergy-dev` compute node.

### Additional Implementation

- Populated Salt Jin heat-balance reference rows from:
  - `reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/case_metric_summary.csv`
- Refactored dense candidate scoring:
  - old behavior: one worker scored one candidate by solving Salt 2, Salt 3,
    and Salt 4 serially
  - new behavior: one task is one `(candidate, salt)` solve, so dense grids are
    parallelized at the actual coupled-solve level
- Updated reusable launch template:
  - `tmp/2026-07-01_rom_model_form_jobs/run_compact_model_form_fits.slurm`
  - now requests 64 tasks and runs `--grid-level compact --workers 64`

### Additional Commands

- `python3 -m pytest tools/analyze/test_rom_model_form_fits_and_1p4_boundary.py -q`
  - result: `5 passed`
- `python3 -m py_compile tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py`
  - result: passed
- `env MPLCONFIGDIR=tmp/2026-07-01_rom_model_form_jobs/mplconfig python3 tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py --grid-level compact --workers 64`
  - result: completed at `2026-07-01T17:29:07-05:00`
  - approximate wall time: about 24 minutes on `c318-008`

### Compact Dense Fit Results

Current package now reflects `grid_level=compact`, not the earlier selected
surrogate run.

- Best compact dense form:
  - `fit_major_k90_1p4`
  - fit family: `two_parameter_fit`
  - coefficients: `major_loss_multiplier=2.1`, `k90=0.0`, `k20=0.0`
  - objective RMSE mdot error: `3.594%`
  - mean absolute mdot error: `3.103%`
  - mean energy error: `14.027%` of heater
- Nearly tied simpler form:
  - `fit_major_defaultK_1p4`
  - coefficients: `major_loss_multiplier=2.1`, `k90=1.0`, `k20=0.1`
  - objective RMSE mdot error: `4.583%`
  - mean absolute mdot error: `3.145%`
  - mean energy error: `14.057%` of heater
- Bend-only form:
  - `fit_k90_major1_1p4`
  - coefficients: `major_loss_multiplier=1.0`, `k90=12.5`, `k20=0.0`
  - mean absolute mdot error: `4.865%`
- Claude casewise CFD closures at `1.4 in`:
  - mean absolute mdot error: `13.915%`
  - mean energy error: `14.229%` of heater
- Default `1.4 in` rad-on:
  - mean absolute mdot error: `35.393%`
  - mean energy error: `13.735%` of heater

### Interpretation After Compact Fit

- The dense compact mdot optimum is at the edge/interior combination
  `major=2.1`, `k90=0`. That says the mdot objective alone can trade bend losses
  against major-loss multiplier strongly; it does not prove the physical bend K
  is zero.
- The nearly tied `major=2.1` with default minor K is easier to defend than a
  zero-bend optimum because its mdot performance is almost the same and it keeps
  the known fittings in the model.
- Energy error is now populated for Salt 2-4 Jin, but it does not yet select the
  same winner as mdot. Default `1.4 in` has poor mdot but similar energy error
  to the fitted closures. This reinforces that model selection must be
  multi-objective: mdot, pressure/resistance distribution, temperatures, and
  heat balance.
- Several Salt 4 rows remain `accepted_for_validation=False`; do not hide this
  in paper-facing tables.

### Full Dense Fit Note

Do not start the full dense fit as an incidental local command. The compact run
already took about 24 minutes with 64 workers. The full grid is about an order
of magnitude larger and should be run as a scheduled allocation job after one
more decision about objective function:

- mdot-only objective is useful for quick closure screening
- paper-facing objective should include mdot, segment pressure distribution,
  TP/TW temperature errors, heat-balance error, and root/validity penalties
- if keeping mdot-only for the full grid, record it explicitly as a hydraulic
  calibration diagnostic, not a validated ROM
