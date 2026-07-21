---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md
tags: [openfoam, salt4, high-heat, recirculation, run-prep]
related:
  - .agent/status/2026-07-16_AGENT-471.md
  - .agent/journal/2026-07-16/high-heat-no-recirc-probe.md
task: AGENT-471
date: 2026-07-16
role: Implementer/Tester/Writer
type: campaign
status: active
---
# High-Heat No-Recirculation Probe

This campaign stages and submits one Salt4 Jin continuation probe:
`salt4_q3x_no_recirc_probe`.

The target heater input is `1012.8 W`, equal to `3.0 x` Salt4 nominal and
`2.73 x` the current `salt4_hi10q` maximum of `371.36 W`. This is an
aggressive onset bracket, not an admitted prediction that recirculation will
disappear. Existing +/-5% and +/-10% rows still show material reverse flow.

## Cooler / Convergence Policy

The run scales the three fixed cooler/sink `Q` patches by the same factor as
the heater:

- `pipeleg_upper_04_reducer`
- `pipeleg_upper_05_cooler`
- `pipeleg_upper_06_reducer`

This keeps the imposed source/sink contract close to the parent operating
point's balance. Leaving the cooler at the old setting would create a large net
positive heat input and make convergence much less meaningful.

Runtime controls follow the repaired corrected-Q pattern: explicit integer
restart, `timeFormat general`, `timePrecision 6`, and diagnostic-only
`convergenceMonitor`.

## Reproduce / Inspect

```bash
/usr/bin/python3.11 jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/stage_high_heat_probe.py
bash -n jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_q3x_no_recirc_probe.sbatch
```

## Submission

Submitted job: `3299610`.

Early check: `RUNNING` on `c318-017`.

Monitor:

```bash
squeue -j 3299610
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-salt4_q3x_probe-3299610.out
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/runs/salt4_jin_q3x_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_high_heat_probe
```

## 500 / 1000 / 1500 W Bracket Pack

Submitted job: `3299620`.

Cases:

- `salt4_q0500w_no_recirc_probe`: `500 W` total heater input.
- `salt4_q1000w_no_recirc_probe`: `1000 W` total heater input.
- `salt4_q1500w_no_recirc_probe`: `1500 W` total heater input.

Cooling is scaled patchwise from the Salt4 nominal parent by
`target_heater_power_W / 337.6 W`. The batch launcher copies `processors64`,
patches the collated restart `T`, runs restart-level preflight, and only then
launches `foamRun`.

Monitor:

```bash
squeue -j 3299620
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-salt4_heat_pack-3299620.out
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/logs/bracket_runtime_preflight_3299620.csv
```

## Steady-State Relaunch Pack

Submitted job: `3308712` on `2026-07-21`.

The relaunch combines the timed-out high-heat cases into one 256-task pack:

- `salt4_q0500w_no_recirc_probe`: restart `11658`
- `salt4_q1000w_no_recirc_probe`: restart `11031`
- `salt4_q1500w_no_recirc_probe`: restart `10795`
- `salt4_q3x_no_recirc_probe`: restart `11395`

This is a continuation for steady-state evidence, not an admitted closure or a
no-recirculation prediction. The relaunch uses the latest completed
`processors64/<time>/T` fields from jobs `3299610` and `3299620`, preserves the
corrected high-heat source/sink patch contract, and keeps `timeFormat general`
with `timePrecision 6`.

Pre-submit and in-job preflight both passed with `4` audited cases and
`0` failures:

- `logs/steady_relaunch_pre_submit_preflight.csv`
- `logs/steady_relaunch_runtime_preflight_3308712.csv`

Monitor:

```bash
squeue -j 3308712
sacct -j 3308712 --format=JobID,JobName%30,State,ExitCode,Elapsed,Timelimit,NodeList%30
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-salt4_heat2_pack-3308712.out
tail -f jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/runs/salt4_jin_q0500w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_high_heat_steady_relaunch
```

Expected terminal review: after success or timeout, claim a separate
harvest/disposition row before reconstructing, postprocessing, using endpoint
fields for F6/recirculation decisions, or making any admission claim. The first
steady-state check should repeat the mdot/temperature/heat drift assessment on
the latest written window; `q0500` had the best hydraulic drift before relaunch,
but all cases still had material thermal/heat drift.
