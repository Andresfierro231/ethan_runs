# Corrected Salt Q Perturbations

Date: `2026-07-04`

## 2026-07-13 Naming And Admission Correction

Current working names omit the historical staging suffix:

- `salt2_jin_lo10q_corrected` -> `salt2_lo10q`
- `salt2_jin_hi10q_corrected` -> `salt2_hi10q`
- `salt4_jin_lo10q_corrected` -> `salt4_lo10q`
- `salt4_jin_hi10q_corrected` -> `salt4_hi10q`

The source `*_corrected` keys remain in manifests, registry rows, and case paths
as provenance for the repaired staging workflow. Tables and launcher logs should
use the short names when presenting the current run plan.

Coordinator policy correction: if a Salt-Q perturbation row is converged or has
a stationary terminal window, it is closure-fit admissible. The older
post-restart-advance `too_short` label is retained only as run-history context
for converged rows and must not by itself exclude them from closure fitting.

## Purpose

This campaign replaces the June 19/25 Salt Q perturbation runs as closure-fit
inputs. The old perturbation roots are quarantined as invalid data because the
intended Q perturbation was not present in the decomposed restart fields read by
`foamRun`; some root `0/T` files also changed only one of the three lower
heater patches.

The invalid roots must not be used for closure fitting, Re-response fitting, or
1D-model validation. They may be cited only as evidence of the workflow failure:
the metadata/root fields advertised a perturbation, but the restart field that
the solver actually read remained nominal.

## Correction

Each corrected case is staged from the nominal Salt Jin continuation, records
the exact `SOURCE_PROCESSORS64.txt`, and patches:

- root `0/T`;
- the copied `processors64/<latest>/T` restart field immediately before
  `foamRun`;
- all three lower heater patches:
  `pipeleg_lower_04_straight`, `pipeleg_lower_05_straight`,
  `pipeleg_lower_06_straight`;
- the three balanced cooling sink patches:
  `pipeleg_upper_04_reducer`, `pipeleg_upper_05_cooler`,
  `pipeleg_upper_06_reducer`.

## Admission Rule

These runs are admissible when the terminal monitors show convergence /
stationarity at the perturbed operating point. The expected Q-response direction
and a re-plateau remain the scientific checks; a post-restart-advance duration
threshold alone is no longer an exclusion for an otherwise converged row.

## 2026-07-13 Four-Row Packed Continuation

The final available Salt4 +10Q window from the interrupted `3288671.5`
continuation was not steady enough to postprocess as terminal evidence. Over
`12039` to `12639 s`, the `salt4_hi10q` total heat residual drifted by
`-1.59099 W` on a `7.71885 W` mean, the four sampled mass-flow monitors drifted
by about `1.13e-4 kg/s` each (`~0.61%` of mean) with `~2.4%` window spans, and
temperature/wall-temperature probe drifts reached `1.45105 K` and `1.52954 K`.

The selected continuation launcher therefore packs four 64-rank cases on one
256-task node:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`
- `salt4_hi10q`

The script refuses to launch more than four cases or more case ranks than the
allocated tasks. It patches the selected restart `T` field from the manifest
before launch, starts selected integer restarts explicitly, and keeps the
historical `*_corrected` keys only as source-path provenance.

### 2026-07-13 Time-Name Precision Repair

Job `3293441` did not fail from flow divergence or scheduler failure. All four
`foamRun` steps aborted in `Foam::Time::operator++()` when adaptive stepping at
large restart times produced fractional names such as
`10291.0613496932601`, and `timeFormat general` with `timePrecision 12` could
not distinguish the next time directories without risking overwrite.

The durable launcher rule is now:

- patch the intended integer restart `T` explicitly from the manifest;
- verify that the requested processor restart directory exists and is the
  intended integer restart (`10291`, `9674`, `11655`, `12639` for the current
  four-row wave);
- use `startFrom startTime` with that exact integer `startTime`;
- use `timeFormat general` and `timePrecision 6`, matching the July 10 Salt4
  repair that advanced from an integer restart after higher precision failed;
- run `tools/analyze/check_corrected_salt_preflight.py` with runtime-control
  checks before launching `foamRun`.

Three rejected intermediate fixes are documented because they should not be
repeated. Raising `timePrecision` to `17` while keeping `timeFormat general`
still failed because OpenFOAM tried to increase precision to `18`, beyond its
maximum. Switching to `timeFormat fixed` while forcing `startFrom startTime`
failed because OpenFOAM looked for a fixed-formatted start-time directory
instead of the existing integer restart directory. Switching to
`timeFormat fixed` with `startFrom latestTime` also failed because the fixed
format still made OpenFOAM look for a rendered time directory that did not
match the integer restart. The correct combination is the explicit integer
`startTime` plus `timeFormat general`/`timePrecision 6` preflight above.

Tomorrow pickup for live job `3293924` is documented in
`operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md`.
Open that note before monitoring, harvesting, or rerunning this selected
continuation wave.

## Submission Record

- `3275388`-`3275391`: failed in preflight because strict shell mode treated
  the TACC/OpenFOAM module bootstrap as a failure before launcher diagnostics.
  No corrected case `processors64` tree was created.
- `3275392`-`3275395`: canceled because Slurm `--export` split comma-separated
  case lists, so group 1 received only the first case. The partial
  `salt1_jin_lo10q_corrected/processors64` copy was removed before resubmission.
- `3275400`-`3275403`: canceled after launch-time patching exposed a third
  launcher defect. After OpenFOAM sourcing, `python` resolved to a broken
  Python 3.9 module, and the function did not enforce patcher failure before
  continuing to `foamRun`. The contaminated staged `runs/` tree was deleted and
  regenerated from clean nominal continuations.
- `3275422`-`3275425`: canceled after the restart-field patcher was found to
  text-rewrite a collated `decomposedBlockData` `T` file and corrupt its
  per-processor byte framing. The patcher now preserves the binary/collated
  wrapper and recomputes each processor block byte count, matching the existing
  insulation true-steady patching pattern. The contaminated staged `runs/` tree
  was again deleted and regenerated.
- `3275433`-`3275436`: canceled after Salt1 cases still failed at coded
  function-object startup. The staged roots had omitted parent `dynamicCode/`,
  forcing each parallel case to compile coded function objects during launch.
  The staging script now copies parent `dynamicCode/`; patcher stdout is also
  redirected out of the restart-time capture path.
- `3275448`-`3275451`: current corrected submission as of this note. Group 1
  (`3275448`) had both Salt1 cases running past dynamic-code startup and writing
  timesteps; groups 2-4 were pending.
- Current corrected submission: see `submitted_jobs.csv`. The launcher now uses
  `/usr/bin/python3.11` by default and aborts the case before `foamRun` if
  launch-time restart patching fails.
- `2026-07-07` Salt 1 review: `salt1_jin_hi10q_corrected` did not stop because
  it reached `controlDict` `endTime`. `controlDict` still had
  `stopAt endTime` and `endTime 9756.33125`; the run stopped at
  `4010.590361446 s` because the included `system/functions`
  `convergenceMonitor` called `stopAt(writeNow)` after a weak global
  `Tmean`/`Tsigma`/`Umean` drift criterion passed. Salt 1 corrected-Q rows
  remain non-admissible. The Salt 1 corrected case `convergenceMonitor`
  entries have been changed to diagnostic-only so a future continuation cannot
  terminate on this global monitor; admission still requires operating-point
  movement plus quasi-steady time-window UQ.

## Reproduce / Inspect

```bash
python jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/stage_corrected_cases.py
bash -n jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_packed_corrected_salt_q.sbatch
bash -n jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/submit_corrected_jobs.sh
squeue -j "$(awk -F, 'NR>1 { ids = ids ? ids "," $2 : $2 } END { print ids }' jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv)"
```

Local smoke artifacts:

- `root_patch_audit.csv`: root `0/T` patch audit for every corrected case.
- `work_products/2026-07-04_salt_perturbation_bc_audit/restart_field_smoke_audit.csv`:
  sampled restart-field patch audit; every target patch appears 64 times in the
  collated decomposed `T` file copy.
- `work_products/2026-07-04_salt_perturbation_bc_audit/binary_frame_smoke/`:
  binary-frame smoke copy used to verify that patching preserves all 64
  collated processor block boundaries.

Additional pre-submit rule for continuation waves:

- Inspect `system/controlDict` and every included function-object file before
  submission. For perturbation-response runs, coded monitors may log diagnostic
  convergence, but they must not call `stopAt(writeNow)` unless the task
  explicitly approves early termination on that monitor.
- For large-time adaptive continuations repaired from integer restart
  directories, use the documented July 10 pattern: explicit integer
  `startTime`, `timeFormat general`, and `timePrecision 6`. The preflight
  should reject mismatched restart directories, `latestTime` for selected
  explicit restarts, fixed-format restart attempts, and higher general-format
  precision.
