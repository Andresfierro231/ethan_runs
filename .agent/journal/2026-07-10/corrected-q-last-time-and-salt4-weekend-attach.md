# Corrected-Q Latest-Time Reporting and Salt4 Weekend Attach

Date: 2026-07-10
Role: Coordinator / Implementer / Tester / Writer

## Summary

The corrected-Q registry table builder now reports all registered corrected-Q
rows with both gate time and current case-root/log time. Salt4 +10Q corrected
was repaired and attached to the underfilled selected corrected-Q allocation
`3288671` as step `3288671.5`.

## Latest-Time Table

The regenerated selected table is:

`work_products/2026-07/2026-07-10/2026-07-10_registry_corrected_q_status_table/selected_corrected_q_status_table.md`

The complete all-row latest-time CSV is:

`work_products/2026-07/2026-07-10/2026-07-10_registry_corrected_q_status_table/corrected_q_latest_timesteps.csv`

At final regeneration, the selected rows showed:

| Row | Gate latest time | Latest written timestep | Latest log time |
| --- | --- | --- | --- |
| Salt1 -10Q corrected | `6377.610 s` | `6543.000 s` | `6543.435 s` |
| Salt1 +10Q corrected | `4010.590 s` | `4165.000 s` | `4165.705 s` |
| Salt4 +10Q corrected | `11536.798 s` | `11537.000 s` | `11537.723 s` |

These remain perturbation rows for sensitivity/correlation support only.

## Capacity Decision

`sacct` showed:

- `3288671`: selected corrected-Q allocation, 256 CPUs on `c318-017`; before repair attach it had two running 64-rank solver steps and one failed 64-rank Salt4 step, leaving about 128 free cores.
- `3282992`: Salt1 nominal allocation, 256 CPUs on `c318-016`; one 64-rank solver step, leaving about 192 free cores.

I attached Salt4 +10Q to `3288671`, not `3282992`, because it is the same
corrected-Q campaign allocation and had enough spare capacity.

## Salt4 Repair

The original Salt4 +10Q failed as `3288671.2` at OpenFOAM time name
`11536.488262910847` with maximum time precision reached.

Repair attempts:

- `3288671.3`: `timeFormat fixed` caused OpenFOAM to look for
  `11536.000000000`, while the clean restart directory is `11536`; failed before
  solver advancement.
- `3288671.4`: `timePrecision 16` still failed at the same maximum-precision
  check.
- `3288671.5`: `timeFormat general`, `timePrecision 6`, `startFrom startTime`,
  `startTime 11536`; running at final check and advanced beyond the prior
  precision-failure time, with latest table regeneration showing `11537.000 s`
  written and `11537.723 s` logged.

Final observed Slurm state included:

- `3288671.0` RUNNING: Salt1 -10Q corrected.
- `3288671.1` RUNNING: Salt1 +10Q corrected.
- `3288671.5` RUNNING: repaired Salt4 +10Q corrected.

## Next Checks

- Monitor `3288671.5` through the weekend with `sacct -j 3288671` and the
  Salt4 attach log.
- Do not re-attach more Salt4 attempts unless `3288671.5` fails.
- After job exit, harvest terminal logs/postProcessing and rerun corrected-Q
  gate diagnostics before any admission decision.
- Keep all corrected-Q rows out of nominal baseline and closure-fit use unless
  explicit gate evidence admits them.
