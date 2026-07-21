# CFD / 1D Geometry-BC Contract And Run Plan

Date: `2026-07-08`
Task: `AGENT-205`
Role: Coordinator / Writer

## Summary

Wrote
`operational_notes/07-26/08/2026-07-08_cfd_1d_geometry_bc_contract_and_run_plan.md`
as the durable contract for current Salt-family CFD/1D geometry and boundary
condition interpretation.

The note records:

- the CFD setup label:
  `1.4in_layer_present__surface_emissivity_bc_present_no_volume_radiation_field`;
- why `0.25 in` / `0.30 in` belong to 1D diagnostic sweeps, not CFD setup;
- the 1D geometry and scenario contract from the Fluid model code/configs;
- current corrected-Q live windows and gate dependency;
- Salt 1 base-continuation status;
- non-duplicative future run candidates.

## Evidence Read

- `work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv`
- `work_products/2026-07-08_cfd_scenario_contract/latest_window_audit.csv`
- `work_products/2026-07-08_cfd_scenario_contract/README.md`
- `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/scenarios.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/campaigns.yaml`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/job_groups.tsv`
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/campaign_manifest.csv`
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/submitted_jobs.csv`

## Commands

```bash
python3.11 tools/analyze/monitor_live_corrected_salt.py --output-dir tmp/2026-07-08_AGENT-205_live_monitor --gate-job-id 3280969 --dependency afterany:3275448:3275449:3275560
squeue -j 3275448,3275449,3275560,3280969 -o '%i|%j|%T|%M|%l|%R'
sacct -j 3259065,3259066,3259067,3259068,3259069 --format=JobID,JobName,State,Elapsed,Start,End,ExitCode -P
```

## Findings

- Gate job `3280969` is pending on `afterany:3275448:3275449:3275560`; the ID
  and dependency are consistent with the current accepted terminal-job set.
- Live monitor scanned all 14 corrected Salt cases and reported 4 special
  scrutiny rows: Salt1 lo10, Salt1 hi10, Salt3 hi5, Salt3 hi10.
- Salt1-low and Salt4-high are already running in the corrected-Q wave, so they
  are not good duplicate submissions unless the gate later fails them.
- Salt3 hi5/hi10 are the clearest future rerun candidates because their old
  canceled job products advanced only about 20 s and carry fatal/error markers.
- June 25 Salt1 base-continuation Slurm jobs `3259065`-`3259069` were canceled
  before running, but the staged base-continuation tree itself reaches
  `4026.15625 s` and ends cleanly via `convergenceMonitor`; use it as a later
  qualification candidate, not as evidence of completed June 25 chain compute.

## Follow-Up

After `3275448`, `3275449`, and `3275560` finish, run the formal gate `3280969`
and let that gate determine which corrected-Q cases need rerun or extension.
Do not admit corrected-Q rows to closure fitting from live-monitor status alone.
