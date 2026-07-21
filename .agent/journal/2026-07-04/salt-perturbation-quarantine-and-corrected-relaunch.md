# Salt Perturbation Quarantine and Corrected Relaunch

Date: `2026-07-04`
Task: `AGENT-178`
Role: Coordinator / Implementer / Writer

## Observed failure

The historical Salt Q perturbation runs cannot be used as closure-fit data. A
BC audit found that the solver restart field did not reliably contain the
intended Q perturbation. In the old Salt3 +/-5% roots, `case_config.yaml`
advertised changed heater powers, but the decomposed restart `T` field used by
`foamRun` still carried nominal Q values on the lower heater patches. Some root
`0/T` files also changed only `pipeleg_lower_04_straight` while leaving
`pipeleg_lower_05_straight` and `pipeleg_lower_06_straight` nominal.

Interpretation: the pinned mdot is not evidence that the physics or solver is
insensitive to Q. The production restart fields were effectively nominal, so
the old perturbation rows are invalid data. Their only valid use is documenting
the workflow failure.

## Insulation setting

The Jádyn Salt runs inspected here use the baseline insulation setting
`insulated.h = 5.964` in `case_config.yaml`. Historical labels such as
`hiins`/`loins` are misleading for current evidence because that live insulation
knob did not change in those perturbation roots. Treat those old labels as
quarantined perturbation provenance, not as validated insulation variants.

Clarification: `insulated.h` is a heat-transfer coefficient, not a heat-transfer
resistance. Lower `h` means a more insulating exterior convective boundary, but
the effective wall resistance in these cases is patchwise and combines external
convection/radiation with explicit layer conduction from `thicknessLayers` and
`kappaLayerCoeffs` in `0/T`. The authoritative thermal setup is the OpenFOAM
`T` boundary field, not the summary scalar in `case_config.yaml` alone.

Relevant boundary-condition classes:

- `rcExternalTemperature`: custom layered wall BC used on most exterior wall
  segments and powered heater sections. It carries `h`, `Ta`, `Tsur`,
  `emissivity`, `internalRadius`, `thicknessLayers`, material coefficients, and
  sometimes imposed `Q` plus `powerLayer`.
- `externalTemperature`: fixed heat-transfer / fixed heat-loss surrogate used
  on cooler/reducer and other calibrated sink/source patches. The upper cooler
  balance in the corrected Q perturbations lives here.

Lesson: do not describe an insulation variant by `case_config.yaml` labels or
`insulated.h` alone. Audit the actual `0/T` and restart-time
`processors64/<latest>/T` boundary fields for the patch group being claimed.

## Corrected workflow

Created campaign:
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`.

The corrected workflow:

- stages 14 Salt Q perturbation cases from the nominal Jin continuations;
- writes exact `SOURCE_PROCESSORS64.txt` provenance for each case;
- patches all three lower heater patches and the three balanced upper cooling
  patches in root `0/T`;
- patches copied `processors64/<latest>/T` immediately before `foamRun`;
- records root patch audits and restart-field smoke audits;
- keeps the new rows inadmissible until mdot moves from nominal by the expected
  Q response and re-plateaus.

The corrected workflow intentionally restarts from the nominal converged
continuations rather than from a fresh cold start. This is the right mode for
local operating-point perturbations because it preserves the converged thermal
inventory and lets the simulation measure the response to a small Q change. A
fresh initial-condition run would be useful as an independent verification, but
it would spend days re-reaching the nominal state before producing useful
perturbation data. The required safety rule is therefore not "never restart";
it is "restart only from a clean staged copy whose restart boundary fields are
audited before `foamRun`."

Local smoke checks:

- `bash -n` passed for the packed Slurm launcher and submitter.
- `python -m py_compile` passed for the patch/staging scripts.
- `root_patch_audit.csv` reports `root_patch_ok=True` for all 14 cases.
- `work_products/2026-07-04_salt_perturbation_bc_audit/restart_field_smoke_audit.csv`
  reports `ok=True` for all 14 cases, with 64 target entries per patch in the
  sampled collated decomposed `T` field copy.
- Binary-frame smoke test passed for a copied collated `decomposedBlockData`
  restart `T` file: all six target patches were patched in 64 processor blocks,
  and every processor block byte-count frame remained valid.

Permanent preflight gate for future agents:

1. Confirm `case_config.yaml` records the intended operating point.
2. Confirm root `0/T` changed every intended patch, not just the first matching
   patch.
3. Confirm copied `processors64/<latest>/T` changed every intended patch,
   because that is what `foamRun` reads on restart.
4. For collated `decomposedBlockData`, patch with a frame-preserving parser and
   verify all processor block byte counts remain valid.
5. Confirm `preflight_patch_audit_<job>.csv` exists before treating a launched
   job as valid.
6. Keep all outputs provisional until mdot moves from nominal by the expected Q
   response and re-plateaus.

## Submission history

- `3275388`-`3275391`: failed in 3 seconds before diagnostics because strict
  shell mode treated the TACC/OpenFOAM module bootstrap as a failure. Fixed by
  matching the existing successful launchers: disable `set -eu` while sourcing
  OpenFOAM, capture the source status, then explicitly verify `foamRun`.
- `3275392`-`3275395`: canceled after group 1 stdout showed only one case. Root
  cause was Slurm `--export` splitting comma-separated case lists. Fixed by
  exporting only `CASE_GROUP` and reading the case list from `job_groups.tsv`
  inside the launcher. Removed the partial `processors64` copy left in
  `salt1_jin_lo10q_corrected` before resubmission.
- `3275400`-`3275403`: canceled after launch-time patching exposed another
  launcher defect. After OpenFOAM sourcing, `python` resolved to a broken
  Python 3.9 module. The function also failed to enforce the patcher return code
  because it later returned the restart-time command status, allowing `foamRun`
  to start without a guaranteed restart-field patch. Fixed by using
  `/usr/bin/python3.11`, explicitly aborting on patcher failure, deleting the
  contaminated staged `runs/` tree, and regenerating clean staged roots.
- `3275422`-`3275425`: canceled after `foamRun` reported a corrupted
  collated restart `T` file. Root cause: the launch-time patcher text-rewrote
  an OpenFOAM `decomposedBlockData` file without preserving the per-processor
  byte-count framing. Fixed by adding binary-safe collated patching that
  rewrites each processor block and recomputes its byte count. Verified on a
  copied restart field: all six target patches patched in 64 processor blocks,
  and all 64 processor block boundaries remained valid. Deleted and regenerated
  the staged `runs/` tree again after this bad attempt.
- `3275433`-`3275436`: canceled after the Salt1 cases still failed at coded
  function-object startup. The parent nominal continuation had reusable
  `dynamicCode/`; the corrected staging script had omitted it and forced fresh
  parallel dynamic-code compilation. Fixed by staging parent `dynamicCode/` and
  redirecting patcher stdout so restart-time capture stays clean.
- `3275448`-`3275451`: current corrected submission. At the last check,
  groups `3275448`, `3275449`, and `3275450` were running, with their `foamRun`
  steps active; `3275451` was pending for resources. `3275448` had all four
  packed group-1 cases launched, and the Salt1 cases were writing timesteps
  past dynamic-code startup.
- User-requested footprint reduction on 2026-07-04: canceled `3275451`, then
  canceled only Salt3 high-Q steps `3275450.0` and `3275450.1` inside
  `3275450`. This leaves `3275450.2` and `3275450.3` running the Salt4 low-Q
  cases on `3275450`. Submitted delayed replacement `3275558` from `login3` as
  `corr_saltq_g4_delayed` with dependency `afterany:3275450`; it will run the
  Salt4 high-Q pair through the normal `sbatch` launcher after `3275450`
  exits, not from an interactive shell.
- Immediate correction to the previous operational change: user clarified that
  `3275450` itself should be canceled and replaced by one normal `sbatch` job
  containing only Salt4 cases. Canceled `3275450` and canceled pending
  `3275558`. Added `corr_saltq_salt4_all` to `job_groups.tsv` with exactly the
  four Salt4 cases (`lo10q`, `lo5q`, `hi5q`, `hi10q`) and submitted replacement
  `3275560` from `login3`. Scheduler and audit checks showed `3275560` running
  on `c318-018` with four live 64-rank `foamRun` steps; each Salt4 case wrote
  `preflight_patch_audit_3275560.csv` with `root_patch_ok=True` and
  `processor_patch_ok=True`.
- Current corrected submission: see
  `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv`.

## Related jobs

Water postprocess remains queued as dependency job `3275363`
(`afterany:3265970`) so it runs after the active Water continuation exits. The
next 1D model-form job `3275364` completed successfully; a local `srun` copy
also produced outputs under
`work_products/2026-07-04_consolidated_closure_and_model_jobs_local/`.

## Remaining checks

After corrected Salt jobs launch solver ranks, inspect per-case
`logs/log.foamRun_corrected_q` and `preflight_patch_audit_<job>.csv`. After they
produce late windows, rerun the perturbation operating-point gate and admit only
rows marked `requalified` into closure fitting or 1D model comparisons.

## Monday handoff

Current queue state at closeout:

- Water continuation `3265970` is still running; `water1` completed, `water2`,
  `water3`, and `water4` remain active. Water postprocess job `3275363` is
  pending on `afterany:3265970`.
- 1D model-form job `3275364` completed successfully.
- Corrected Salt Q jobs: `3275448`, `3275449`, and `3275450` are running;
  `3275451` is pending for resources.

Final closeout update before footprint reduction: a later queue check showed
`3275451` had started. All four corrected Salt Q jobs `3275448`-`3275451` were
running, and their visible `foamRun` steps were active. Later same-day
operational update: `3275451`, `3275450`, and `3275558` were canceled; Salt4
replacement job `3275560` is running all four Salt4 perturbation cases through
the normal packed `sbatch` launcher. Water `3265970` was still running;
dependent Water postprocess `3275363` remained pending on `afterany:3265970`.

## 2026-07-07 Salt 1 Run-Control Lesson

Coordinator review found that `salt1_jin_hi10q_corrected` stopped cleanly after
only `254.259 s` of corrected-Q advance because the included coded
`system/functions` `convergenceMonitor` called `stopAt(writeNow)`. This was not
an `endTime` stop: `system/controlDict` still specified `stopAt endTime` and
`endTime 9756.33125`, while the final solver time was `4010.590361446 s`.

The Salt 1 corrected low/high Q `system/functions` entries were changed so the
monitor remains diagnostic but no longer calls `stopAt(writeNow)`. The log
message now says the diagnostic criterion was met and the run is continuing to
configured `endTime`; corrected perturbation admission remains a post-run gate
based on operating-point movement and quasi-steady time-window uncertainty.

Lesson for future OpenFOAM continuation waves: inspect both `controlDict` and
included function-object dictionaries before submission. `stopAt endTime` in
`controlDict` is not sufficient if an included coded function object can mutate
run control. For perturbation-response or relaxation-history runs, global
volume-mean convergence monitors must not be terminating unless the task
explicitly approves that early-stop criterion.

Monday continuation steps:

1. Check `sacct` and per-case `logs/log.foamRun_corrected_q` for
   `3275448`, `3275449`, canceled `3275450`/`3275451`/`3275558`, and Salt4
   replacement `3275560`. Do not assume success from job state alone.
2. Verify every corrected case has `preflight_patch_audit_<job>.csv` with
   `root_patch_ok=True`, `processor_patch_ok=True`, and processor patch counts
   of `64` for all six target patches.
3. After the jobs produce late monitor windows, run the perturbation
   operating-point gate. Rows that are stationary but did not move from nominal
   are still invalid.
4. When Water `3265970` exits, confirm dependent postprocess `3275363` ran and
   publish/freeze the resulting Water summary before using it in model fitting.
5. Update the consolidated closure table and 1D model comparison only with rows
   that have an explicit admissibility status.
6. Build a reusable automated preflight checker for future restart campaigns.
   It should fail a case unless `case_config.yaml`, root `0/T`, and
   `processors64/<latest>/T` agree for every target thermal patch; verify all
   target patch counts; preserve/verify collated `decomposedBlockData` frames;
   and write a documented audit artifact that future agents can cite.
