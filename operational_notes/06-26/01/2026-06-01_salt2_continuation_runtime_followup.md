# 2026-06-01 salt2 continuation runtime follow-up

## Observed output

- Original continuation job `3200407` failed with exit code `127`.
- The staged continuation log confirmed the immediate failure mode: every rank wrote `foamRun: command not found`.
- The container submission wrapper in `jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_andres2d_container_template.sbatch` used the older `bash -lc` pattern even though the archived integration notes explicitly recommend `--cleanenv` plus a non-login shell.
- I corrected that wrapper to use `/bin/bash --noprofile --norc -c` and to fail fast on `command -v foamRun`.
- Resubmitted continuation job `3200937` started on `c318-016` and failed with exit code `1:0`, not `127`.
- The corrected job no longer appended new `foamRun: command not found` lines to `logs/log.foamRun_continuation`; instead it failed before entering the solver command path.
- A compute-side probe job `3200970` tested the original OpenFOAM 13 bashrc path from the source log: `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13/etc/bashrc`.
- Probe job `3200970` also failed with exit code `1:0` and produced no `BASHRC_OK` marker, which is consistent with the original OpenFOAM 13 bashrc path not being readable from the current compute-side environment.

## Inferred interpretation

- The first continuation failure was a real launcher bug in the container wrapper, and that specific bug is now fixed.
- The continuation path is still blocked, but now by runtime availability rather than shell invocation syntax.
- The `andres_2d` container image remains unsuitable as currently wired for this 3D restart because the sourced OpenFOAM environment still does not expose a usable `foamRun` command for this case.
- The original native OpenFOAM 13 runtime from the source log also does not appear directly reusable from the current workspace environment.
- The staged case data itself is not the blocker at this point; the blocker is locating a runnable OpenFOAM environment compatible with the case and `libRCWallBC.so`.

## Contradictions / risks

- The container launch path was previously treated as a likely bridge to continuation, but the corrected job still does not reach the solver.
- Falling back to TACC's available `openfoam/12` module would be a version change from the source run and should not be assumed safe without an explicit compatibility decision.
- Repeated resubmission without a verified runtime path would burn allocation time without advancing the case.

## Next suggested actions

- Locate a readable OpenFOAM 13 runtime or a container image that exposes `foamRun` correctly for this workflow.
- Verify compute-side readability of the candidate runtime before the next continuation submission.
- Keep all restart experimentation inside `jadyn_runs/salt2/2026-06-01_continuation_candidate/`.
- Do not refresh salt2 QoI products until a continuation checkpoint is actually written.
