# 2026-06-02 ethan_runs

## Observed Output

- Completed a variant-aware publish pass for the first staged `modern_runs` batch into the sibling publication workspace at `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-02_ethan_modern_runs_first_batch_v1/`.
- The published contract now keeps Jin and Kirst as separate comparison rows while mapping both back to shared base tests `salt_test_1` through `salt_test_4`.
- Corrected the local run-status parser so normal OpenFOAM endings are recognized even when `End` and `ExecutionTime` appear on different lines. This reclassified `viscosity_screening_salt_test_1_kirst_coarse_mesh` and `viscosity_screening_salt_test_2_kirst_coarse_mesh` from false `incomplete` status to `completed` with recorded convergence.
- Rebuilt local extraction tables and campaign summaries under `work_products/campaigns/2026-06-01_modern_runs_first_batch/`. Current local counts are `2` completed/converged cases and `10` terminated/non-converged cases.
- Generated a water-laminar claim audit under `reports/2026-06-02_water_laminar_claim_audit/`. All four water laminar cases currently classify as `needs_convergence_audit`.
- Downloaded the official OpenFOAM 13 and ThirdParty 13 source trees into persistent storage under `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/`, then created the stable canonical alias `/work/09748/andresfierro231/ls6/OpenFOAM-13`.
- Successful runtime recovery milestones:
  - Build `3202515` completed successfully.
  - Probe `3202516` completed successfully and confirmed compute-side `foamRun` at `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/OpenFOAM-13/platforms/linux64GccDPInt32Opt/bin/foamRun`.
  - The same probe confirmed readable `libRCWallBC.so` under `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data`.
- Continuation submission history for `val_salt_test_2_coarse_mesh_laminar`:
  - `3202687`: first continuation relaunch reached the batch shell but failed inside the `srun` step because `foamRun` was not resolved on the launched ranks and Intel MPI lacked PMI wiring. This job was cancelled after diagnosis.
  - `3202708`: corrected relaunch now uses the resolved `foamRun` path plus `srun --mpi=pmi2` and `I_MPI_PMI_LIBRARY=/usr/lib64/libpmi2.so`. As of `2026-06-02T11:43-05:00`, it is running and has entered OpenFOAM startup through `Create mesh for time = 1724`.

## Inferred Interpretation

- The missing `foamRun` problem was not a single file issue. The real requirement was a compute-validated OpenFOAM 13 runtime plus a matching MPI bootstrap path on LS6.
- The stable name that should now be used in docs and future submissions is `/work/09748/andresfierro231/ls6/OpenFOAM-13`. The dated recovery directory remains underneath it for provenance and may later be replaced or repointed if your coworker provides the original private runtime tree.
- The `andres_2d` container path is still not an adequate substitute for this case. It exposes a different OpenFOAM family/version than the original salt logs.
- The first modern publish pass remains structurally aligned with the requested contract rule: Jin and Kirst are separate rows, but explicitly tied to the same base salt-test contracts.
- The water laminar cases are acceptable for preliminary trend inspection only. They are not yet acceptable validation-claim rows because none recorded the coded convergence marker, and `water_test_4` is especially weak due to its shorter final runtime.

## Contradictions / Risks

- The continuation wrapper is now past the earlier PATH and PMI failures, but the job is still in early runtime. We still need the first real post-restart timestep/write evidence before calling the restart fully successful.
- Only two salt viscosity-screen rows are currently publish-ready as `comparison_candidate` rows: `salt_test_1_kirst` and `salt_test_2_kirst`. The remaining salt rows still require convergence audit or restart/continuation decisions before paper-facing interpretation.
- The four water laminar rows should not be treated as accepted claims until a convergence audit or continuation path is completed.

## Next Suggested Actions

- Monitor continuation job `3202708` for the first successful timestep progression and the first clean write after restart.
- If `3202708` stabilizes, let it run as the active salt2 continuation chunk and reassess QoIs after a meaningful new checkpoint lands.
- If your coworker replies with the original private runtime tree or bootstrap recipe, compare it against the fallback `/work/.../OpenFOAM-13` path before deciding whether to repoint the canonical alias.
- Keep the analysis-only fallback branch documented: if the continuation later proves numerically unstable or runtime-incompatible, stop forcing runtime work and fall back to extracted-data analysis only.
- For the terminated salt modern-batch rows, separate likely divergence from likely near-steady-state shortfall before deciding whether to continue/restart them or keep them as non-claim audit rows.

## Ethan OpenFOAM 13 Bootstrap Reference

### Observed Output

- Ethan reported that `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13` is a standard OpenFOAM 13 install with no special solver modifications.
- Ethan shared the bootstrap order used on TACC:
  1. `source /work/09807/ethanrozak/ls6/OpenFOAM_V13/of13-env.sh`
  2. `unset FOAM_SIGFPE`
  3. solver launch
- Ethan's shared `of13-env.sh` semantics are:
  - `module purge`
  - `module load TACC`
  - `module load gcc/13.2.0`
  - `module load impi/21.12`
  - `export WM_MPLIB=INTELMPI`
  - `export MPI_ROOT=${I_MPI_ROOT}`
  - `source .../OpenFOAM-13/etc/bashrc`
  - `module load python3/3.9.7`
  - prepend `/opt/apps/gcc11_2/python3/3.9.7/lib` to `LD_LIBRARY_PATH`
- Direct filesystem comparison against Ethan's actual `/work/09807/...` tree is still blocked from this account by `Permission denied`, even after the shared-path note.
- A compatibility test against the local canonical runtime alias `/work/09748/andresfierro231/ls6/OpenFOAM-13` shows that Ethan's core bootstrap sequence resolves `foamRun` and `foamRun -help` correctly here.
- The only bootstrap mismatch observed locally is that `module load python3/3.9.7` does not load cleanly under the same active toolchain on this account; it is therefore treated as optional in the local reusable env script.
- Added reusable bootstrap script `jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh` to mirror Ethan's sequence against the local canonical runtime alias.
- Updated the continuation wrapper for future submissions so it sources that env script and unsets `FOAM_SIGFPE` before launch.

### Inferred Interpretation

- The local runtime appears aligned enough with Ethan's description to be treated as the same practical OpenFOAM 13 family/bootstrap path for current recovery work.
- A true file-for-file comparison is still pending readable access to Ethan's actual `/work/09807/...` tree.
- The most important imported detail from Ethan's note was not a custom solver patch but the exact launch order and environment semantics.

## Metadata And Closure Infrastructure

### Observed Output

- Generated a durable assumptions/geometry index at `reports/2026-06-02_ethan_case_metadata_index/`.
- Generated a closure/steady-state scaffold at `reports/2026-06-02_ethan_closure_and_visualization_scaffold/`.
- The metadata index covers `13` cases: the active salt2 case plus the first staged modern-runs batch.
- The metadata index records geometry inventory, operating points, boundary-condition assumptions, convergence settings, fluid-property model types, and available 1D/2D insulation/reference fields when present in the published contract.
- The closure scaffold currently marks:
  - `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`
  as immediate closure/steady-state candidates.
- The closure scaffold marks `val_salt_test_2_coarse_mesh_laminar` as `active_continuation`.

### Inferred Interpretation

- We now have a durable local handoff layer for later 1D/2D comparison, closure-term derivation, and steady-state visualization work.
- The reports are sufficient to stop rediscovering case assumptions from raw trees each time downstream analysis starts.

## Salt2 Continuation Runtime Recovery Progress

### Observed Output

- Continuation job `3202708` remains running on `c318-018`.
- The corrected relaunch is past the earlier PATH/PMI startup failures and is now advancing solver time.
- Current log tail shows live progression at least through:
  - `Time = 1777.92 s`
  - `Time = 1777.925714286 s`
  - `Time = 1777.931428571 s`
- Residuals, continuity errors, and Courant output are present, which confirms the continuation is in real timestep advancement rather than merely startup.

### Inferred Interpretation

- The salt2 continuation path is now genuinely recovered at the runtime/bootstrap layer.
- The next useful checkpoint is no longer "can it start?" but "does it continue cleanly long enough to produce a meaningful new checkpoint/write for QoI reassessment?"

## Visualization Kickoff For Converged Kirst Cases

### Observed Output

- The closure scaffold already identifies the two immediate steady-state visualization candidates as:
  - `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`
- Both rows are marked `completed`, `convergence_reached=True`, and `comparison_candidate` in the local metadata index.
- Staged durable render-job wrappers for both cases under `staging/render_jobs/` so the field-figure workflow can be launched reproducibly through Slurm rather than ad hoc local commands.
- Added a campaign note at `reports/2026-06-02_kirst_visualization_campaign/README.md` documenting targets, outputs, and resubmission commands.

### Inferred Interpretation

- The first visualization pass should focus on these two Kirst rows because they are the only current salt rows that both completed normally and satisfied the coded convergence monitor.
- The right next product is not interpretation yet but durable rendered field figures, staging manifests, and output status files under the existing render pipeline.

## Ethan 1D Model Discrepancy Pass

### Observed Output

- Compared the shared 3D run-side salt property assumptions in Ethan's staged `case_config.yaml` files against the current 1D model branches in the sibling `tamu_first_order_model/Fluid` workspace.
- Verified that the current 1D default remains `salt_current`, which uses tabulated interpolation from `SALT_ROWS`.
- Verified that the current 1D workspace also contains a `salt_promoted` branch, but it is a Jin-style promoted branch rather than a Kirst-style branch.
- Verified that the converged shared 3D Kirst runs use:
  - constant `Cp = 1423.47 J/kg-K`
  - `k(T) = 0.78 - 1.25e-3*T + 1.6e-6*T^2`
  - `rho(T) = 2293.6 - 0.7497*T`
  - viscosity `mu_spec.type = expInvT` with coefficients `[6.757e-05, 2247.11]`
- Verified that the shared 3D Jin runs use the same `Cp`, `k`, and `rho`, but a different viscosity branch:
  - viscosity `mu_spec.type = expInvT` with coefficients `[0.001149, -810.896, 780600]`
- Verified that the current 1D predictive outputs already include both:
  - `salt_current` predictive contract rows
  - `salt_promoted` predictive comparison rows
- Wrote a durable report package under `reports/2026-06-02_ethan_1d_model_discrepancy_report/`.

### Inferred Interpretation

- The main discrepancy is not only "Ethan tweaked the 1D model." The current 1D workspace contains at least three materially different salt-property stories:
  - current default tabulated `salt_current`
  - promoted Jin-style `salt_promoted`
  - shared 3D Kirst-style constant-`Cp`/polynomial-`k`/linear-`rho` with a different exponential viscosity law
- That means we should not describe the current 1D model as matching Ethan's converged Kirst runs, even though both use constant `Cp`.
- The next 1D reconciliation step should be an explicit Kirst-style property branch or a variant-aware 1D reporting contract, not a vague "promoted salt" label.

## Explicit TODOs

- Monitor `3202708` until a meaningful new continuation checkpoint/write lands, then rerun salt2 QoI extraction and reassessment.
- Submit and monitor the two Kirst visualization jobs; once they finish, review whether the first rendered figures are sufficient or whether additional field selections and section cuts are needed.
- Run the new explicit `salt_kirst` branch through the stage-1 predictive scenario for at least Salt 1 and Salt 2, then compare those 1D outputs against the converged Kirst CFD rows.
- Investigate whether Ethan's shared run trees contain any archived 1D scripts beyond the 3D-side property/config evidence; if not, keep the discrepancy report explicitly scoped to shared-run assumptions plus the current 1D workspace.
- After the visualization outputs exist, start reduced closure extraction for the two converged Kirst rows and connect those products to later 2D/1D comparisons.

## Kirst Visualization Submission Status

### Observed Output

- Submitted first-pass render jobs for the two converged Kirst cases:
  - `3203083` -> `viscosity_screening_salt_test_1_kirst_coarse_mesh_render.sbatch`
  - `3203084` -> `viscosity_screening_salt_test_2_kirst_coarse_mesh_render.sbatch`
- Current scheduler state at submission check:
  - `3203083`: `PENDING (Priority)`
  - `3203084`: `PENDING (Priority)`
- Active salt2 continuation remains healthy at the same check:
  - `3202708`: `RUNNING` on `c318-018`
  - latest inspected solver log progressed through `Time = 1806.857142857 s`

### Inferred Interpretation

- Visualization work is now started as actual queued compute work, not just documentation.
- The next concrete check for this branch is whether the render jobs finish with usable `figures_rendered/<source_id>/status.json` and screenshots.

## Secure OpenFOAM Tree Comparison And 1D Search

### Observed Output

- Read `/scratch/secure/nuclear/OpenFOAM_V13/of13-env.sh` and confirmed it matches the bootstrap sequence Ethan described earlier.
- Confirmed `/scratch/secure/nuclear/OpenFOAM_V13/` contains a standard `OpenFOAM-13/` plus `ThirdParty-13/` layout and does not expose an obvious archived TAMU loop 1D model.
- The tree search found only stock OpenFOAM/tutorial-style `1D` or `first` paths, not a separate Ethan reduced-order model or TAMU loop 1D workflow.
- Verified the current local persistent alias remains in place at `/work/09748/andresfierro231/ls6/OpenFOAM-13` and points to the dated fallback runtime root.

### Inferred Interpretation

- Ethan's secure shared path is useful as a direct OpenFOAM runtime reference and bootstrap reference, but it is not currently a source of the separate TAMU loop 1D model we were looking for.
- The 1D reconciliation work still needs to proceed in the sibling `tamu_first_order_model/Fluid` workspace unless a different archived Ethan 1D path is shared later.

## Checkpoint — 2026-06-02 (End-of-Day Handoff)

- Salt2 continuation `3202708` remains running and is now progressing through restarted timesteps.
- Restarted continuation evidence is present in `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation` with post-restart writes through processor time folders `1890`–`1894`.
- Kirst steady-state render jobs `3203083` and `3203084` are still queued (`PENDING (Priority)`), and no rendered outputs are yet in `figures_rendered/`.
- 1D reconciliation status is still pending; the discrepancy gap remains between shared 3D Kirst/Jin assumptions and current default 1D property branches.

### Tomorrow TODOs

- Confirm continuation state and job health for `3202708`, then decide whether to let it continue or stop at a defensible checkpoint.
- Capture the first meaningful continuation write/checkpoint, then run updated salt2 QoI extraction against the continuation source path.
- Update continuation-linked handoff artifacts (`work_products`, metadata/closure notes, and campaign summaries) so downstream products follow the latest source location.
- If `3202708` stalls or fails, capture the failure mode and switch to analysis-only fallback only after clear classification of failure cause.
- Recheck `3203083` and `3203084`, then add render-review notes once first-pass images are available.
- Run the explicit `salt_kirst` 1D variant through stage-1 predictive workflow for Salt 1 and Salt 2, then compare against converged Kirst 3D rows.
- Continue searching for any Ethan-shared archived 1D scripts if runtime/shared-tree access changes.
- Keep water laminar cases in `needs_convergence_audit` unless new solver output appears; do not move them into claims.
