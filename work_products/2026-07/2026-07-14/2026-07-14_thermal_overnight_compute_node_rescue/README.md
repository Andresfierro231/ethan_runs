---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_tomorrow_thermal_parity_and_overnight_study_handoff/overnight_study_queue.csv
  - work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/overnight_study_recommendations.csv
tags: [thermal-parity, forward-model, overnight, compute-node]
related:
  - operational_notes/07-26/14/2026-07-14_TOMORROW_THERMAL_PARITY_AND_OVERNIGHT_STUDY_HANDOFF.md
  - operational_notes/07-26/14/2026-07-14_TOMORROW_FORWARD_V1_FULL_CONTEXT_AND_OVERNIGHT_PLAN.md
task: AGENT-392
date: 2026-07-14
role: Scheduler/Writer
type: work_product
status: complete
---
# Thermal Overnight Compute Node Rescue

This package launches the non-overlapping lightweight thermal/forward-model
studies requested for overnight execution directly on compute node `c318-008`.
It was created as a rescue package because `AGENT-391` initially appeared on
the board with the same intent but had no status file and no live background
process. Before launch, `AGENT-391` did become active, so this runner was
narrowed to the missing thermal lanes and avoids duplicate mdot/sensor sweeps.

The runner does not launch OpenFOAM solvers, mutate native CFD outputs, edit
registry/admission state, or edit external Fluid source.

## Runner

```bash
bash work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/run_thermal_overnight_background.sh
```

Launched in the background with `nohup`; see:

- `runner.pid`
- `logs/nohup.out`
- `command_manifest.csv`
- `stage_status.csv`
- `run_summary.json` after completion

Actual launch and completion:

- First `nohup` attempt wrote a manifest and stale PID but no live process.
- Relaunched in detached tmux session `ag392_thermal` on
  `2026-07-15T07:50:31-05:00`.
- Runner PID: `2114243`.
- Completed: `2026-07-15T07:53:14-05:00`.
- Runtime: about 2 min 42 sec.
- Stages: 8.
- Failed stages: 0.
- `external_bc_refresh`, `setup_only_hx_fit`, `heater_fraction_refresh`,
  `heat_loss_discrepancy_refresh`, and focused tests all exited `0`.

Monitor:

```bash
tmux ls
ps -f -u andresfierro231
tail -20 work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/stage_status.csv
cat work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/run_summary.json
```

## Stages

1. `external_bc_refresh`: external-BC and thermal-profile parity refresh.
2. `external_bc_tests`: focused external-BC unit test.
3. `setup_only_hx_fit`: setup-only predictive HX fit refresh.
4. `setup_only_hx_tests`: focused predictive HX fit unit test.
5. `heater_fraction_refresh`: split-aware heater/source-contract refresh.
6. `heater_fraction_tests`: focused heater/source-contract unit test.
7. `heat_loss_discrepancy_refresh`: best-current heat-loss discrepancy refresh.
8. `heat_loss_discrepancy_tests`: focused heat-loss discrepancy unit test.
9. `mdot_temperature_and_sensor_policy`: not run here; covered by active
   `AGENT-391` output at
   `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/`.

All outputs remain diagnostic until the relevant admission/score gates
explicitly admit them.

## Parallel Completed Runner

`AGENT-391` completed the mdot/temperature queue with exit code `0` at
`2026-07-14T18:09:19-05:00`:

- `agent360_refresh`
- `setup_only_cooler_closure_bakeoff`
- `test_section_boundary_form_bakeoff`
- `reference_state_temperature_audit`
- `pressure_root_solver_quality_audit`

Path:
`work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/`.
