---
provenance:
  - imports/2026-07-16_high_heat_no_recirc_probe.json
  - imports/2026-07-16_high_heat_bracket_pack_500_1000_1500.json
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_probe_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_bracket_pack_manifest.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/
tags: [high-heat, salt4, recirculation, cfd-harvest, live-monitor]
related:
  - .agent/status/2026-07-17_AGENT-485.md
  - imports/2026-07-17_high_heat_harvest_readiness_and_live_monitor.json
task: AGENT-485
date: 2026-07-17
role: Coordinator/cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# High-Heat Harvest Readiness And Live Monitor

## Why This Exists

The Salt4 high-heat CFD jobs are running and should not be harvested as if they
were terminal. This task created a small read-only monitor and harvest contract
so tomorrow's work can decide when to postprocess without mutating native solver
outputs or relying on chat history.

## Files To Open First

- `work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/README.md`
- `work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/live_job_status.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/required_qoi_contract.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/postprocess_command_plan.md`

## Observed State

Final live refresh reported both parent Slurm jobs as `RUNNING` by read-only
`sacct`: `3299610` (`salt4_q3x_probe`) and `3299620` (`salt4_heat_pack`).
All four cases have passed runtime preflight and have active/recent foamRun
logs. No case is currently terminal or harvest-ready.

Indexed total heater inputs are `500 W`, `1000 W`, `1012.8 W`, and `1500 W`.
The bracket cases use the documented cooler scaling policy from
`imports/2026-07-16_high_heat_bracket_pack_500_1000_1500.json`.

## Output Contract

Each terminal case should produce the fields and derived rows listed in
`required_qoi_contract.csv`: `U`, `T`, `wallHeatFlux`, `Re`, `Pr`, `Ri`, `Gr`,
`Ra`, `Gz`, wall-core Delta T, reverse area fraction, reverse mass fraction,
secondary velocity fraction, steady-window status, and mesh/time uncertainty.

## Next Task Sequence

1. Refresh `live_job_status.csv` with:
   `python3.11 tools/analyze/build_high_heat_harvest_readiness_and_live_monitor.py`
2. If either job remains `RUNNING`, monitor only.
3. If a job is terminal and successful, claim a new extraction task before
   running any postprocessing that creates artifacts from native solver outputs.
4. Use `postprocess_command_plan.md` and `required_qoi_contract.csv` as the
   extraction contract.
5. Treat any material reverse-flow case as onset/recirculation evidence, not as
   an ordinary single-stream upcomer `Nu`, `f_D`, or component `K` fit row.

## Blockers And Guardrails

The main unresolved blocker is terminal availability: none of the four cases is
ready to harvest yet. The monitor records scheduler query diagnostics in
`scheduler_query_diagnostics.json`; sandboxed SSH can fail with a local SSH
config permission error, so the final package was refreshed with approved
read-only scheduler access.

Do not mutate native solver outputs, do not update registry/admission state, do
not cancel/resubmit these jobs from this package, and do not run generated docs
index refresh while active AGENT-482 owns that scope.
