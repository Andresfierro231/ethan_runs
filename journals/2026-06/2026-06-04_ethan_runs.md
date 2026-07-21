# Ethan Runs Update

Date: 2026-06-04

## Observed Outputs

- Generated the June 4 reporting package with one reproducible script: `tools/analyze/build_ethan_report_package.py`.
- Wrote direct CFD-vs-experiment metrics to `reports/2026-06-04_ethan_direct_validation/`.
- Wrote the expanded metadata/glossary package to `reports/2026-06-04_ethan_case_metadata_index/`.
- Wrote the runtime-decision and alternate-case package to `reports/2026-06-04_ethan_runtime_and_hypothesis_matrix/`.
- Added per-case direct validation summaries under `work_products/<source_id>/direct_validation_summary.json`.

## Interpretation

- `val_salt_test_2_coarse_mesh_laminar` now resolves to the active continuation runtime tree under `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`.
- The active continuation is still running under job `3202708`, with current extracted time about `3207 s`.
- The metadata index now distinguishes the native continuation salt2 case from the staged viscosity-screening salt2 rows by runtime root, parsed 3D insulation thickness, viscosity coefficients, and cooler-h difference.
- The metadata README now explains the `two_d_*`, `one_d_stage*`, `cp_coeff_count`, `rho_coeff_count`, and `final_total_wall_heat_abs_w` fields explicitly.
- The direct validation package now gives 3D CFD-vs-experiment RMSE for every Ethan row.

## Contradictions / Caveats

- Temperature RMSE is moderate-to-large for the salt rows, but the dominant mismatch is external loss: every salt row remains roughly two orders of magnitude low against the Ethan-linked external-loss proxy.
- Because the validation table does not publish one single direct measured ambient-loss column, the new `exp_q_external_loss_*` comparison uses the Ethan prescribed segment-loss reconstruction (`qambient_total_W`) from `validation_imposed_ethan_v2`.
- The `two_d_radiation_on` and `one_d_stage*` fields are comparison-scenario metadata only; they are not direct proof that the native 3D run was configured with those exact switches.

## Suggested Next Actions

- Let `val_salt_test_2_coarse_mesh_laminar` continue; it remains the only justified runtime extension target.
- Do not submit the staged non-converged salt rows just to run longer. Their late-window drifts are already small while validation mismatch remains severe.
- Prioritize radiation-on and wall-loss-treatment sensitivity cases before any thicker-insulation alternate for the salt rows.
- Start the next pass on time-history and steady-state behavior analysis using the decision matrix outputs as the case triage layer.

## Later Same-Day Update

- Corrected the direct heat-loss comparison basis in `reports/2026-06-04_ethan_direct_validation/`.
- The previous external-loss comparison used the net `total_Q` wall sum, which mixes heating, cooling, and ambient exchange.
- The updated report now derives a 3D ambient-loss proxy from `postProcessing/wallHeatFlux/1/wallHeatFlux.dat` and exports section totals plus raw `experiment - simulation` channel errors for `TP`, `TW`, and `mdot`.
- Under that corrected basis, the salt rows are no longer ~99% low on ambient loss. They are now roughly ~17-27% low on the Ethan-linked ambient-loss proxy, while the mass-flow shortfall remains roughly ~15-31% depending on row.
- `TW10` is currently the dominant wall-temperature error station across the salt rows.

## Later Same-Day Update 2

### Observed Outputs

- Regenerated `reports/2026-06-04_ethan_direct_validation/` after explicitly excluding `TW10` from `exp_tw_rmse_k` and `exp_all_temp_rmse_k`.
- Generated the reusable Salt 2 behavior package with `tools/analyze/build_salt2_behavior_package.py`.
- Wrote Salt 2 shared-axis plots, setup comparison, full time-series CSV, late-window summary CSV, and a scientific README to `reports/2026-06-04_salt2_behavior_package/`.

### Interpretation

- With `TW10` excluded, Salt 2 wall RMSE is much tighter and easier to interpret as a comparison of the remaining wall stations.
- Updated Salt 2 wall RMSE values are:
  - `val_salt_test_2`: `6.2627 K`
  - staged Salt 2 Jin: `6.6153 K`
  - staged Salt 2 Kirst: `6.9717 K`
- Updated combined temperature RMSE values are:
  - `val_salt_test_2`: `5.1959 K`
  - staged Salt 2 Jin: `5.6223 K`
  - staged Salt 2 Kirst: `6.1410 K`
- `val_salt_test_2` remains the best Salt 2 row on TP RMSE and mdot error.
- `val_salt_test_2` uses effectively constant `Cp = 1423.47 J/kg-K`.
- For subsequent Salt 2 runs, the current recommended default basis is the `val_salt_test_2` setup:
  - hotter start (`T_init = 451.5 K`)
  - thicker outer insulation (`1.65 in`)
  - slightly lower cooler `h` (`28.577 W/m^2-K`)
  - Jin-style viscosity branch as the starting point
- The active continuation tree has mixed time coverage:
  - mdot, TP, and TW probe outputs currently extend through `1724 s`
  - `wallHeatFlux` extends through about `3295 s`
  - late-window statistics in the Salt 2 behavior package are therefore metric-specific by construction

### Caveats

- `TW10` is still exported as a raw signed `experiment - simulation` error in the direct-validation CSV, but it is intentionally excluded from RMSE scoring and that exclusion is now explicit in the documentation.
- The `val_salt_test_2` continuation case does not yet provide continued probe/mdot histories beyond the pre-continuation window, so TP/TW/mdot trend comparisons do not yet cover the full continuation tail.

### Suggested Next Actions

- Treat the Salt 2 behavior package as the base layer for the next steady-state audit.
- If new continuation probe outputs appear for `val_salt_test_2`, rerun both June 4 scripts to refresh the late-window probe behavior.
- Prioritize section-wise drift interpretation and steady-window classification before proposing any new Salt 2 alternates beyond the adopted `val_salt_test_2` defaults.

## Later Same-Day Update 3

### Observed Outputs

- Wrote a practical residual-based audit for the salt rows to `reports/2026-06-04_ethan_essential_steadiness_audit/`.
- The audit uses late-window mdot drift, late-window probe drift, and the final net `|total_Q|` residual as a fraction of heater power, instead of relying only on the coded convergence flag.

### Interpretation

- The collaborator concern about false convergence is supported for the Salt 1 rows, but not for the full salt batch.
- Salt Test 1 Jin and Salt Test 1 Kirst are flat in the tail, yet both still sit on a net heat-balance residual floor of about `9.46-9.49 W`, or about `4.1%` of heater power. Those should not be treated as clean steady-state rows.
- Salt Test 2, 3, and 4 rows are much stronger on a practical-steadiness basis. Their final net `|total_Q|` residuals are all below about `0.33%` of heater power, with tiny late-window mdot and probe drifts.
- `val_salt_test_2_coarse_mesh_laminar` is already usable now under this practical criterion even though its coded convergence flag is still false, because its current tail is flat and its final net residual is only about `0.24%` of heater power.
- The main practical exception outside Salt 1 is `viscosity_screening_salt_test_4_jin_coarse_mesh`, which is still usable but should be treated as borderline because its mdot late-window drift is larger than the other Salt 2-4 rows.

### Suggested Next Actions

- Use Salt Test 2, 3, and 4 for current steady-state analysis, with a caveat on Salt 4 Jin.
- Do not treat Salt Test 1 Jin or Salt Test 1 Kirst as good-enough steady-state rows without additional runtime or a deeper enthalpy-residual explanation.
- Keep separating two questions in later reports: `coded convergence reached?` and `practically steady enough to use?`.

## Later Same-Day Update 4

### Observed Outputs

- Staged a writable Salt 4 Jin continuation candidate under `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/`.
- Submitted the background Salt 4 Jin continuation with a `72:00:00` walltime cap as Slurm job `3208600`.
- Generated `reports/2026-06-04_all_salt_behavior_package/` with:
  - `all_salt_case_status.csv`
  - `all_salt_steady_window_summary.csv`
  - `ambient_loss_audit.csv`
  - `jin_vs_kirst_summary.csv`
  - `representative_case_selection.csv`
- Added manuscript-facing Ethan CFD sections and provenance notes under `../papers/dmdc_analysis/` and verified the paper builds through the module-based `latexmk` path.

### Interpretation

- Salt 4 Jin is now the actively extended sensitivity representative, while Salt 4 Kirst remains the steadiest current reference row.
- The all-salt package reinforces the earlier pattern that Jin-versus-Kirst changes mdot agreement much more than it changes the ambient-loss proxy.
- The Salt 2 triad remains the clearest evidence that the residual ambient-loss mismatch is driven mainly by a shared wall-loss-model bias rather than by viscosity choice, modest insulation changes, or the slightly lower cooler `h` alone.
- Current representative-case policy is now explicit in `representative_case_selection.csv`:
  - Salt 1: no steady-state representative yet; Jin is the preferred continuation candidate
  - Salt 2: `val_salt_test_2_coarse_mesh_laminar`
  - Salt 3: manuscript preference `viscosity_screening_salt_test_3_jin_coarse_mesh`
  - Salt 4: current steady reference `viscosity_screening_salt_test_4_kirst_coarse_mesh`, manuscript sensitivity representative `viscosity_screening_salt_test_4_jin_coarse_mesh`

### Suggested Next Actions

- Build the next extraction pass for section pressure drops from saved `p_rgh` fields.
- Build axial heat-transfer reductions by section so the manuscript can report `q_w(x)`, `T_w(x)`, `T_bulk(x)`, and derived `Nu(x)` or `h(x)`.
- Continue deepening the manuscript sections in `../papers/dmdc_analysis/` using the new all-salt package as the run-state and representative-case source.

## Later Same-Day Update 5

### Observed Outputs

- Generated `reports/2026-06-04_ethan_section_transport_package/` with:
  - `section_pressure_drops.csv`
  - `pressure_surface_values.csv`
  - `section_heat_drift.csv`
  - `section_heat_latest.csv`
  - `representative_section_summary.csv`
  - `scientific_writeup_notes.md`
- The package uses non-destructive reconstruction of latest-time `p` and `p_rgh` fields for all salt rows, followed by patch-averaged pressure reductions on the major non-conformal interface patches.
- The first Salt 4 Jin background continuation submission (`3208600`) failed immediately because the continuation launcher used a dummy parallel Pstream runtime.
- A second Salt 4 Jin continuation submission (`3208837`) got past the dummy-Pstream issue after switching to the full OpenFOAM 13 `bashrc`, but then failed immediately on a runtime `libstdc++` / `GLIBCXX_3.4.32` mismatch.

### Interpretation

- The section-pressure results are clean enough for branch-scale hydraulic interpretation now, even though a fully transient pressure-history workflow is still pending.
- Across the usable Salt 2-4 rows, the largest `|Δp_rgh|` is consistently in the upper leg, followed by the left and right legs. The lower leg and the test-section branch are much smaller on a `p_rgh` basis.
- Jin-versus-Kirst differences are now visible hydraulically: for Salt 2-4, Jin usually reduces the upper-leg and left-leg `|Δp_rgh|` relative to Kirst, which is directionally consistent with Jin's better mdot agreement in the validation package.
- The late-window section-heat drift ranking shows that the junction-region wall heat and the derived ambient-loss proxy are usually the most mobile residual channels. The main heater, cooling branch, downcomer, and upcomer terms are much flatter in the late window for the practically steady rows.
- The section-transport package therefore strengthens the current manuscript narrative in two ways:
  - the remaining validation mismatch is not just a global mdot problem; it has a branch-resistance structure
  - the remaining late-time thermal movement is concentrated more in junction-region and ambient-loss channels than in the main heater/cooler branch totals
- The Salt 4 Jin extension request is still technically unresolved. The case itself remains analyzable from current outputs, but the background continuation launcher now has two environment-level failures that must be fixed before any further resubmission claim is made.

### Caveats

- The package intentionally stops short of full axial `h(x)` or `Nu(x)` reporting because the reconstructed root-level `T` field is not yet reliable enough for generic surface sampling in this workflow.
- Pressure-drop signs in the new CSV follow geometric `start -> end` patch ordering. The absolute columns should be used for loss ranking unless a later flow-direction convention is explicitly imposed.

### Suggested Next Actions

- Use the new section-pressure rows and section-heat drift rows as source material for the hydraulic and thermal-network parts of the manuscript.
- Build a compute-node postprocessing path for transient `p_rgh` histories and axial wall/bulk temperature sampling so the report can move from branch-scale metrics to distance-resolved transport coefficients.
- Treat the Salt 4 Jin continuation as blocked on runtime environment repair, not on case physics or case setup.

## Later Same-Day Update 6

### Observed output
- Confirmed the interactive shell is on `login3.ls6.tacc.utexas.edu`, not on a compute node.
- Patched `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch` to use the same OpenFOAM 13 env-script bootstrap pattern as the working Salt 2 continuation instead of sourcing a raw bashrc directly.
- Resubmitted Salt 4 Jin continuation as Slurm job `3208905`; current queue state is `PD (Priority)`.
- Added `tools/analyze/build_ethan_transient_axial_package.py` and launched it to build all-salt transient histories plus latest-time axial wall-transfer reductions.
- The new package is successfully extracting transient metrics from native outputs and is progressing through latest-time OpenFOAM patch reductions.
- Latest-time axial `T/Nu/wallHeatFlux` reduction succeeds for some rows (including the active `val_salt_test_2` row and staged `salt_test_2_jin`), but some staged rows hit a repeatable FOAM read error when `foamPostProcess` reads reconstructed `T`.
- The axial script was patched so these per-case `T` read failures are recorded in-row as `axial_field_extraction_error` rather than aborting the whole package.

### Interpretation
- The Salt 4 runtime issue was not caused by being on a compute node; it was an environment-bootstrap mismatch. The repaired launcher now follows the Salt 2 pattern closely enough to test that hypothesis directly.
- The transient package itself is straightforward and source-driven; the main fragility is only in the latest-time reconstructed `T` read path used for axial `Nu` and wall-temperature augmentation.
- Even where reconstructed `T` fails, the patchwise axial wall-heat histories from `wallHeatFlux.dat` remain valid and useful for the thermal writeup.

### Contradictions / unresolved issues
- Reconstructed root `T` is still not uniformly readable by `foamPostProcess` across all staged rows, even after the best-effort fallback patch. This looks like a case/file-format issue in the reconstructed scalar field path, not a failure of the source `wallHeatFlux.dat` histories themselves.

### Suggested next actions
- Let the transient/axial package finish so the generated CSVs, plots, and error annotations can be audited case by case.
- Check whether `3208905` reaches `R` and survives the previous `GLIBCXX` failure point.
- If the axial `T` read failures persist in representative staged rows, switch the next refinement to q-profile-first reporting with optional targeted re-postprocessing on selected cases rather than trying to force all rows through the same reconstructed `T` path.

## End-of-Day Checkpoint

### Observed output
- `val_salt_test_2` continuation job `3202708` remains running on `c318-018`.
- Salt 4 Jin continuation was resubmitted as job `3208905` after updating the launcher to use the Salt 2 OpenFOAM env-script bootstrap pattern.
- Salt 4 Jin `3208905` failed quickly with `ExitCode=1:0`.
- A new Salt 1 Jin continuation candidate was staged non-destructively under `jadyn_runs/salt1/2026-06-04_jin_continuation_candidate` using a minimal restart stage (restart state plus required runtime files only).
- Salt 1 Jin continuation was submitted as job `3208956`.
- Salt 1 Jin `3208956` also failed quickly with `ExitCode=1:0`.
- For both Salt 1 Jin and Salt 4 Jin, the Slurm launcher reached the expected OpenFOAM env script, resolved `foamRun`, and printed the expected Intel MPI path, but `logs/log.foamRun_continuation` still shows:
  - `Trying to use the dummy Pstream library.`
  - `This dummy library cannot be used in parallel mode.`
- The new all-salt transient/axial package script is still the active analysis path for transient behavior and latest-time axial reductions. It can tolerate case-specific reconstructed-`T` read failures by recording `axial_field_extraction_error` rather than aborting the whole package.

### Interpretation
- The additional continuations that were scientifically worth trying tonight were Salt 1 Jin and Salt 4 Jin.
- Both are currently blocked by the same runtime/bootstrap issue rather than by case physics or missing restart state.
- That means there are not additional continuation jobs that are honestly "ready to just run" tonight beyond the already-running Salt 2 continuation.
- The immediate next technical task is to resolve the dummy-Pstream parallel runtime issue for the staged Salt 1/Salt 4 continuation copies before resubmitting again.

### Contradictions / unresolved issues
- Salt 2 `3202708` is running successfully under the local OpenFOAM 13 recovery path, while Salt 1 Jin `3208956` and Salt 4 Jin `3208905` fail with dummy Pstream under what appears to be the same env-script bootstrap pattern.
- That implies an unresolved difference remains between the working Salt 2 continuation runtime context and the failing Salt 1/Salt 4 continuation contexts.

### Tomorrow handoff
- See `operational_notes/06-26/05/2026-06-05_todo.md` for the prioritized next-step list.
- Do not submit more continuation jobs until the dummy-Pstream issue is understood and corrected.
