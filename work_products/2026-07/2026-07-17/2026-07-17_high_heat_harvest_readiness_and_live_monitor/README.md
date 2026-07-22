---
provenance:
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_probe_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_bracket_pack_manifest.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/
tags: [high-heat, recirculation, cfd-harvest, live-monitor]
related:
  - .agent/status/2026-07-17_AGENT-485.md
  - .agent/journal/2026-07-17/high-heat-harvest-readiness-and-live-monitor.md
task: AGENT-485
date: 2026-07-17
role: cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# High-Heat Harvest Readiness And Live Monitor

This package indexes the running Salt4 high-heat jobs and defines what to do
when they become terminal. It does not extract native solver outputs and does
not submit, cancel, or stage jobs.

## Current Summary

- Jobs monitored: `2`.
- Cases indexed: `4`.
- Cases harvest-ready now: `0`.
- Running/not terminal cases: `0`.
- Scheduler action: `none_disabled_for_test`.

## Outputs

- `live_job_status.csv`
- `high_heat_case_index.csv`
- `harvest_readiness_queue.csv`
- `required_qoi_contract.csv`
- `postprocess_command_plan.md`
- `failure_modes_and_actions.csv`
- `source_manifest.csv`
- `scheduler_query_diagnostics.json`
- `summary.json`

## Rule

If a case is still `running_not_terminal`, monitor only. Claim a separate
extraction task before running any terminal harvest or postprocessing.
