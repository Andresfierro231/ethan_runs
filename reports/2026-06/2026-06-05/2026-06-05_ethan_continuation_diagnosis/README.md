# Ethan Continuation Diagnosis

Generated: `2026-06-07T15:15:55-05:00`

## Current status

- `3202708` for Salt 2 timed out on June 7 after advancing through about `5292.994285714 s`.
- Salt 4 Jin repaired retry `3210231` is still running and the local continuation log has advanced through about `3434.712871287 s`.
- Salt 1 Jin repaired retries `3210268, 3210761, 3211197` all completed successfully under the repaired bootstrap path.
- Salt 1 Kirst retry `3210760` completed successfully, but follow-on retry `3211199` failed immediately with a missing root-level `T` restart file.
- Salt 4 Jin failed in two distinct environment phases before the repaired retry succeeded:
  1. `3208600` and `3208837` failed during OpenFOAM bootstrap with `gcc --showme:link`.
  2. `3208905` got past that bootstrap issue and then failed at solver startup with the dummy Pstream library in parallel mode.
- Salt 1 Jin `3208956` matches the latest Salt 4 Jin failure signature: dummy Pstream in parallel mode.

## What Salt 4 Jin is using for Cp

- Current Salt 4 Jin property model: `Cp polynomial coefficient array with only c0 active; effectively constant 1423.47`.
- Current viscosity branch: `Jin viscosity variant: mu expInvT law A*exp(b0/T+b1/T^2+...) with coefficients [0.001149, -810.896, 780600]`.
- Current conductivity branch: `kappa polynomial coefficients [0.78, -0.00125, 1.6e-06, 0, 0, 0, 0, 0]`.
- Current density branch: `rho polynomial coefficient array length 8; first two terms active [2293.6, -0.7497]`.

## Interpreted runtime cause

- The validated compute probe and the working Salt 2 continuation both depended on sourcing `etc/bashrc` with `WM_MPLIB=INTELMPI` in the bootstrap path.
- The shared env wrapper exported `WM_MPLIB` before sourcing bashrc, but did not pass it as the bashrc source argument. That was the critical difference behind the earlier Salt 1/Salt 4 failures.
- The repaired bootstrap path is now validated for Salt 1 Jin and Salt 1 Kirst. The remaining live question is scientific/runtime usefulness, not MPI bootstrap correctness.

## Interactive-node guidance

- You do not need an interactive compute node to explain the old dummy-Pstream failures anymore.
- An interactive node becomes useful only if Salt 4 `3210231` fails after substantial runtime or if a new staged restart tree needs rank-by-rank library inspection.

## Recommended next steps

- Keep Salt 4 Jin `3210231` running unless a new runtime fault appears, because it is the only live repaired continuation left today.
- Treat Salt 2 as a defensible timeout rather than an environment failure, then decide whether the extra runtime is still worth another extension.
- Repair the Salt 1 Kirst staged restart tree before any further retry, because `3211199` failed on missing root-level `T`, not on the MPI bootstrap path.
- Refresh convergence, continuation, and wall-loss interpretation packages now that Salt 1 Jin and Salt 1 Kirst each have successful repaired-bootstrap runtime history.

## Key files

- `continuation_job_diagnosis.csv`: scheduler and failure signature table.
- `salt_property_reference.csv`: current Salt 1/2/4 property-model reference table.
- `figures/png/continuation_job_sequence.png`: runtime-failure sequence visualization.

