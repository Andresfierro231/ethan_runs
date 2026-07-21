---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_tomorrow_thermal_parity_and_overnight_study_handoff/overnight_study_queue.csv
  - work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/overnight_study_recommendations.csv
tags: [thermal-parity, forward-model, overnight, compute-node]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/README.md
task: AGENT-392
date: 2026-07-14
role: Scheduler/Writer
type: journal
status: complete
---
# Thermal Overnight Compute Node Rescue

The user requested that the proposed overnight studies run directly in the
background on the current compute node. The shell is on
`c318-008.ls6.tacc.utexas.edu`.

`AGENT-391` appeared with a board row for similar work, but initial inspection
found no status file, no work-product files, no runner source, and no background
Python process. A later recheck found only `runner.pid=67` and an empty
`nohup.out`, with no live PID 67 process. Before AGENT-392 launch, AGENT-391
became active and started `run_mdot_temperature_overnight_compute_node_studies.py`.
AGENT-392 therefore provides a path-isolated complementary launch rather than
editing or duplicating `AGENT-391` files.

The launched AGENT-392 stages are the non-overlapping lightweight repo-local
thermal/forward studies recommended by AGENT-370/374: external-BC parity
refresh, setup-only HX fit, heater/source refresh, and heat-loss discrepancy
refresh, each with focused tests where available. The mdot/temperature and
sensor-policy lane is left to the active AGENT-391 runner. No OpenFOAM solver
is launched.

## Launch Record

- First `nohup` attempt: wrote `command_manifest.csv` and a stale PID, but no
  live process and no `stage_status.csv`.
- Robust relaunch: detached `tmux` session `ag392_thermal`.
- Runner PID: `2114243`.
- Launch timestamp: `2026-07-15T07:50:31-05:00`.
- Last observed active child: PID `2114451`, running
  `tools/analyze/build_predictive_hx_fit.py`.
- Completed: `2026-07-15T07:53:14-05:00`.
- Runtime: about 2 min 42 sec.
- Stages: 8.
- Failed stages: 0.
- All AGENT-392 refresh and focused-test stages exited `0`.

`AGENT-391` completed its parallel mdot/temperature runner with exit code `0`
at `2026-07-14T18:09:19-05:00`, producing `agent360_refresh`,
`setup_only_cooler_closure_bakeoff`, `test_section_boundary_form_bakeoff`,
`reference_state_temperature_audit`, and `pressure_root_solver_quality_audit`.
