# 2026-06-01 ethan_runs

## Observed Output

- Reassessed `val_salt_test_2_coarse_mesh_laminar` against the case-defined convergence controls from `case_config.yaml`:
  - QoI relative tolerance: `1.0e-4`
  - QoI window: `100` samples
- Confirmed the native run was configured for `stopAt endTime` with `endTime 10000`, but the solver log stops at simulation time `1724.714285714 s` with Slurm cancellation and signal `15 (Terminated)`.
- Submitted the staged render retry job on `2026-06-01` as Slurm job `3199773`.
- Render job `3199773` completed successfully from the scheduler perspective, but the render step still produced no figures.
- Updated render status remains `skipped` with reason: `paraview_5_10 failed without output.`

## Inferred Interpretation

- This case should not be treated as a completed validation run.
- The strongest evidence is not just the early termination relative to `endTime`; the monitored quantities are still drifting beyond the case's own QoI tolerance.
- The mass-flow monitors remain reasonably tight across sections, but the last-two-window change is still about `2.68e-4` to `2.69e-4`, which is above the configured `1.0e-4` target.
- The derived external heat-loss signal is much less settled: the last-two-window mean changed by about `3.08%`, and the last 100-sample window spans about `7.60%` of its own mean.
- A continuation run in a separate staged folder is warranted before using this case as paper-facing evidence.

## Contradictions / Risks

- The extracted final mdot values look numerically stable enough to tempt premature interpretation, but the heat-loss QoI does not support that conclusion.
- The current cross-model join shows a large heat-loss mismatch versus the trusted reference row, and that mismatch should not be interpreted physically until the continuation question is resolved.
- The render job now confirms the issue is not just a missing submission path; the current ParaView route still fails without output for this decomposed case.

## Next Suggested Actions

- Stage a dedicated continuation copy under `jadyn_runs/salt2/2026-06-01_continuation_candidate/` and keep the imported source tree read-only.
- Continue from the latest written state in the staged copy rather than altering the imported source directory.
- Re-run the QoI extraction after continuation and only promote the case once mdot, heat loss, and temperature metrics satisfy the configured convergence rule or a documented override.
- Treat visualization as secondary until either MPI-capable rendering or a reconstructed renderable staging path is defined.


## Submission Follow-up

- A writable continuation copy is now staged under `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`.
- I derived the continuation submission pattern from `projects_scratch/cfd-modeling-tools/andres_2d_axisymmetric_testing_heat_loss`, but kept the native `foamRun -parallel` restart model because this case is a full 3D decomposed run, not a wedge case.
- The continuation job itself is not yet submitted because the runtime still requires `libRCWallBC.so`, and that library is not readable from the currently accessible environment.
- Runtime estimate from the solver's own convergence monitor suggests about `7.9` more wall-clock days to drive `dTsigma` to `1e-4` if recent decay continues, and about `14.8` more wall-clock days to reach `endTime 10000` at the current throughput.
- Recommended scheduling plan: restartable `96-120 h` chunks, likely at least two additional chunks.

- I validated the exact `andres_2d` container launch path on compute node `c318-008`: the image starts and `/openfoam/bash.rc` exists, but it resolves to OpenFOAM `2512` and does not provide `rcExternalTemperature` / `libRCWallBC.so` for this imported case.


## Modern Runs Inventory

### Observed Output

- A second source batch was identified at
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs`.
- The batch splits into 2 campaigns:
  - `salt/`: 8 named cases
  - `water/`: 8 named cases
- During this inventory pass, an external `chmod` on the source tree was still
  reported as running.
- Readability snapshot:
  - 10 cases were fully extractable
  - 1 case was partially extractable
  - 2 cases exposed metadata only
  - 3 cases remained blocked

### Inferred Interpretation

- The workspace now has a credible path to become a real multi-case intake
  campaign rather than a one-case diagnostic.
- The salt set should be the first staging target because all 8 cases are
  readable and organized as a clean Jin-vs-Kirst viscosity screen across tests
  `1-4`.
- The water set is likely the most valuable eventual bridge to 1D comparison
  because it spans operating point and turbulence model, but it still needs a
  second inventory pass after permissions stabilize.

### Contradictions / Risks

- The current accessibility map is a point-in-time observation, not a durable
  statement about the source tree, because permissions are actively changing.
- Bulk registration of every visible case would overstate readiness and mix
  stable and unstable sources.

### Next Suggested Actions

- Keep the campaign in inventory-only status for now.
- Re-run the readability audit after the external permission pass settles.
- Stage the 8 salt cases and the 2 fully readable water laminar cases first.
- Use the staged batch to build the first cross-case extraction products and
  comparison tables.


## Modern Runs Intake Execution

### Observed Output

- A second readability audit was run after the permission change advanced.
- Updated state:
  - all 8 salt cases are fully readable
  - all 4 water laminar cases are fully readable
  - all 4 water `kOmegaSSTLM` cases remain setup-only in practice: readable
    metadata, but no `log.foamRun` or `postProcessing/` observed
- The first local staging batch was launched through Slurm as job `3200181`
  (`modern_stage1`).
- A dependent registration/import-manifest job was submitted as job `3200186`
  (`modern_reg1`) with dependency `afterok:3200181`.

### Inferred Interpretation

- The source campaign is now ready for real staged intake.
- The right first operational batch is the 8 salt cases plus the 4 water
  laminar cases.
- The water `kOmegaSSTLM` cases should be treated as setup-only cases until
  actual solver-output trees are available.

### Next Suggested Actions

- Let job `3200181` finish copying the first fully extractable batch into local
  staging.
- Let job `3200186` register those staged copies and build their import
  manifests automatically.
- After registration completes, run the extraction pipeline on the staged batch
  and build campaign-level comparison tables.

## 2026-06-01 Continuation-Readiness Update

### Observed Output

- Located a readable `libRCWallBC.so` source at `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so`.
- This resolves the only previously blocking runtime dependency in `val_salt_test_2_coarse_mesh_laminar` continuation workflow.
- The previous barrier was correctly logged as missing-readability of `libRCWallBC.so` for `rcExternalTemperature` boundary handling.

### Inferred Interpretation

- The continuation path now appears blocked by workflow mechanics (submission ordering, restart file continuity, and allocation choices) rather than missing library availability.
- We can now proceed to prep the next continuation run with the `andres_2d` container pattern plus the local 3D `foamRun -parallel` restart path.

### Next Suggested Actions

- Wire `libRCWallBC.so` into the continuation environment (or module path export) for the staged candidate and submit the next sbatch chunk.
- Re-run the geometry/analysis sanity checks after continuation checkpoint import.
- Keep the source tree immutable; continue operating through `jadyn_runs/salt2/2026-06-01_continuation_candidate`.

## 2026-06-01 Status Checkpoint

### What Was Accomplished Today

- Reassessed `val_salt_test_2_coarse_mesh_laminar` against its own convergence logic and confirmed the imported run is not complete enough for defensible interpretation.
- Quantified why continuation is still needed: the run stopped near simulation time `1724.714285714 s` despite `endTime 10000`, and the monitored QoIs still exceed the configured convergence tolerance.
- Submitted and tracked a render retry job for the staged salt2 case, confirming the remaining visualization issue is a runtime/renderability problem rather than a missing scheduler path.
- Staged a dedicated continuation candidate under `jadyn_runs/salt2/2026-06-01_continuation_candidate/` so restart work can proceed without mutating the imported source tree.
- Built a detailed setup dossier for the salt2 case covering geometry, solver setup, modeling assumptions, initial conditions, boundary conditions, probe locations, and comparison hooks for later 1D vs 3D analysis.
- Audited `modern_runs` under Ethan's external tree, documented the source inventory, and split the campaign into salt, water laminar, and water `kOmegaSSTLM` readiness groups.
- Confirmed that the first actionable multi-case intake batch is the 8 salt cases plus the 4 water laminar cases.
- Submitted the first local staging batch as Slurm job `3200181` and the dependent registration/import-manifest job as `3200186`.
- Recorded the critical runtime unblocker for salt2 continuation: `libRCWallBC.so` is available at `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so`.
- Wrote dated manifests, registry updates, operational notes, and TODO tracking artifacts to keep the intake path reproducible.

### Current State

- `val_salt_test_2_coarse_mesh_laminar` remains an incomplete but valuable diagnostic case.
- The continuation path is now conceptually defined and no longer blocked by unknown library location.
- The main remaining salt2 work is execution-oriented: wire the located library into the runtime, submit the continuation chunk, and reassess QoIs after restart.
- The `modern_runs` campaign has moved from ad hoc discovery into staged intake execution, but extraction and cross-case synthesis are still pending completion of the copy/register jobs.
- Visualization remains secondary to numerical completion; interactive ParaView is likely available, but the headless path still needs either a compatible runtime or a reconstruction/export step.

### Main Risks / Blockers

- Salt2 should still not be used as paper-facing evidence until continuation either satisfies the case-defined convergence rule or a documented override is justified.
- The headless render path for the decomposed 3D case remains unresolved.
- The `kOmegaSSTLM` water cases still appear setup-only and should not be mixed into solver-output comparisons prematurely.
- Campaign throughput now depends on orderly handoff from staging to registration to extraction; skipping that sequence would create provenance drift.

### Priority TODO

- Submit the next salt2 continuation sbatch chunk with `libRCWallBC.so` explicitly wired into the runtime environment.
- Preserve restart provenance by keeping all continuation edits inside `jadyn_runs/salt2/2026-06-01_continuation_candidate/`.
- Re-run QoI extraction immediately after the next continuation checkpoint lands.
- Compare post-continuation mdot, heat-loss, and temperature metrics against both prior salt2 extraction outputs and the trusted reference row.
- Check completion state of jobs `3200181` and `3200186`, then launch extraction on the newly staged modern-runs batch.
- Build campaign-level comparison tables for the staged salt and water laminar cases.
- Keep a separate status line for water `kOmegaSSTLM` cases until actual runtime outputs exist.
- Decide whether visualization effort should go through interactive `run_paraview` inspection first or through a reconstructed/headless export path.

## 2026-06-01 Weekly Status Package And Continuation Submission

### Observed Output

- Prepared a presentation-ready weekly status package under `reports/2026-06-01_weekly_status/`.
- Generated three salt2 diagnostic figures from the imported solver outputs and log-derived convergence monitor:
  - `figures/salt2_convergence_monitor.png`
  - `figures/salt2_qoi_trends.png`
  - `figures/salt2_temperature_snapshot.png`
- Generated a machine-readable weekly summary at `reports/2026-06-01_weekly_status/salt2_weekly_status_summary.json`.
- Updated the continuation wrapper to bind the discovered `libRCWallBC.so` path from `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data`.
- Submitted the next salt2 continuation chunk as Slurm job `3200407` (`jadyn_salt2_cont`).
- Live scheduler state at reporting time:
  - `3200407`: `PENDING` on resources
  - `3200181`: `RUNNING`
  - `3200186`: `PENDING` on dependency `afterok:3200181`

### Inferred Interpretation

- The continuation path is now actively in motion rather than merely staged.
- The weekly package is suitable for status presentation because it separates workflow progress, current quantitative results, and remaining convergence risk.
- Salt2 remains best described as an in-progress continuation case with quantified distance to steady state.

### Quantified Status

- Current limiter remains `dTsigma = 7.73823203e-3` versus target `1.0e-4`.
- The current convergence gap is therefore about `77.4x` above the coded tolerance.
- Fit-based projection from the late-run convergence-monitor tail gives about `7.95` additional days to reach `dTsigma = 1e-4` if the current trend persists.
- The same fit suggests one `120 h` continuation chunk would likely reduce `dTsigma` only to about `5.03e-4`, still above target.
- At the observed throughput, reaching `endTime 10000` from the current endpoint would take about `14.81` additional days if no earlier coded stop occurs.

### Next Suggested Actions

- Monitor job `3200407` and capture the first new continuation checkpoint as soon as it is written.
- Allow `3200181` and `3200186` to finish, then move directly into extraction for the staged modern-runs batch.
- Keep presentation language careful: workflow maturity is high, but salt2 physical interpretation is still conditional on continuation evidence.


## 2026-06-01 Continuation Runtime Follow-up

### Observed Output

- Confirmed the original continuation failure mode for job `3200407`: the container wrapper launched every rank into `foamRun: command not found`.
- Corrected `jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_andres2d_container_template.sbatch` to use a non-login shell (`/bin/bash --noprofile --norc -c`) instead of the broken `bash -lc` pattern.
- Resubmitted continuation as job `3200937`; it failed with exit code `1:0` after the shell-bootstrap fix.
- Submitted compute-side probe job `3200970` against the original OpenFOAM 13 bashrc path from the source log.
- Probe job `3200970` failed without reaching the `BASHRC_OK` marker, so the source-log OpenFOAM 13 bashrc path is not directly readable from the current compute-side environment.

### Inferred Interpretation

- The first continuation failure was a launcher bug and has been fixed.
- Continuation remains blocked by runtime availability, not by staged-case integrity.
- The current container image does not yet expose a usable `foamRun` path for this case, and the original native OpenFOAM 13 path is not currently reusable from this workspace context.

### Next Suggested Actions

- Locate a readable OpenFOAM 13 runtime or an equivalent container path that exposes `foamRun` correctly.
- Avoid further continuation resubmissions until the runtime is validated.
- Keep all restart work inside the staged continuation candidate directory.

## 2026-06-01 modern_runs First-Batch Extraction Completion

### Observed Output

- Completed local inventory and QoI extraction for the 12-case first `modern_runs` batch.
- Generated campaign-level tables under `work_products/campaigns/2026-06-01_modern_runs_first_batch/`.
- Campaign summary counts:
  - 12 extracted cases total
  - 8 salt viscosity-screen cases and 4 water laminar cases
  - all 12 cases have `derived_postprocessing_available`
  - 10 cases report `terminated`, 2 cases report `incomplete`
- The incomplete cases are `viscosity_screening_salt_test_1_kirst_coarse_mesh` and `viscosity_screening_salt_test_2_kirst_coarse_mesh`.

### Inferred Interpretation

- The local workflow is now multi-case validated at the extraction stage.
- The modern first batch is ready for local campaign review, but not yet for canonical publish handoff.
- The immediate publish blocker is comparison-contract maturity, not missing local QoI products.

### Contradictions / Risks

- The current join tool expects canonical base test ids and does not yet express Jin/Kirst variant mapping.
- Two extracted salt cases remain incomplete and should not be folded into strong comparison claims without explicit disposition.

### Next Suggested Actions

- Keep the first batch local while variant-aware join rules are defined.
- Review the incomplete Kirst salt cases separately.
- Continue holding the water `kOmegaSSTLM` family in setup-only status.

## 2026-06-01 Publish Gate Status

- `salt_test_2`: publish handoff deferred pending successful continuation or a documented no-continuation decision.
- `modern_runs` first batch: publish handoff deferred pending variant-aware comparison rules and incomplete-case disposition.

## 2026-06-01 End-Of-Day Checkpoint For Tomorrow Morning

### Exact State To Resume From

- `salt_test_2` continuation is still blocked by runtime availability, not by case staging, restart provenance, or missing `libRCWallBC.so`.
- The original failure mode for job `3200407` was real and understood: the container wrapper used the broken `bash -lc` pattern and every rank hit `foamRun: command not found`.
- That shell-bootstrap bug has already been fixed in `jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_andres2d_container_template.sbatch`.
- The corrected continuation resubmission `3200937` still failed with exit code `1:0`.
- The compute-side probe `3200970` against the source-log OpenFOAM 13 bashrc path also failed, so the original native OpenFOAM 13 runtime is not directly reusable from the current environment as tested today.
- The `modern_runs` first batch is locally extraction-complete:
  - 8 salt viscosity-screen cases
  - 4 water laminar cases
  - campaign outputs under `work_products/campaigns/2026-06-01_modern_runs_first_batch/`
- Publish handoff is intentionally deferred for both `salt_test_2` and the modern first batch.

### Exact Questions Still Open

- What runnable OpenFOAM environment can actually expose a usable `foamRun` command for this continuation case on compute nodes?
- Is there a readable OpenFOAM 13 path elsewhere, or do we need a different container image rather than the current `andres_2d` image path?
- If no OpenFOAM 13 runtime is reachable, is using TACC `openfoam/12` acceptable for a continuation of this source case, or is that version change too risky without a separate compatibility decision?
- For the modern first batch, how should Jin/Kirst salt variants map into the canonical cross-model comparison contract?
- Before any publish handoff for the modern batch, what is the explicit disposition for the two incomplete Kirst salt cases:
  - `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`

### Current Working Conclusions

- Do not resubmit `salt_test_2` again until the runtime question is answered with a compute-validated path.
- Do not refresh `salt_test_2` QoI outputs until a real continuation checkpoint is written.
- Treat the modern first batch as locally review-ready but not publish-ready.
- Treat variant-aware join logic as a real missing comparison rule, not just documentation debt.

### First Things To Check Tomorrow

- Re-read:
  - `operational_notes/2026-06-01_salt2_continuation_runtime_followup.md`
  - `operational_notes/2026-06-01_modern_runs_first_batch_extraction_summary.md`
  - `operational_notes/2026-06-01_publish_handoff_gate.md`
  - `operational_notes/2026-06-01_todo.md`
- Re-check the current launcher and status metadata:
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_andres2d_container_template.sbatch`
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/setup_summary.json`
- Re-open the modern batch campaign outputs:
  - `work_products/campaigns/2026-06-01_modern_runs_first_batch/summary.json`
  - `work_products/campaigns/2026-06-01_modern_runs_first_batch/salt_variant_pairs.csv`
  - `work_products/campaigns/2026-06-01_modern_runs_first_batch/water_laminar_operating_points.csv`

### Recommended Starting Thought Process

- Start with the salt2 runtime question, because that is the only blocker preventing new physical evidence for the continuation case.
- Separate launcher mechanics from solver compatibility:
  - launcher mechanics are partially solved
  - runtime availability is not solved
- Only after the runtime path is either solved or explicitly deferred should we decide whether tomorrow's effort should pivot to variant-aware join design for the modern first batch.
