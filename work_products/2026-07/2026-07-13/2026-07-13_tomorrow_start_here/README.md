---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/README.md
tags: [tomorrow-handoff, doc-continuity, forward-model, scheduler-handoff, predictive-1d]
related:
  - operational_notes/07-26/13/2026-07-13_TOMORROW_START_HERE.md
  - .agent/status/2026-07-13_AGENT-307.md
  - .agent/journal/2026-07-13/tomorrow-start-here.md
task: AGENT-307
date: 2026-07-13
role: Coordinator/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Tomorrow Start-Here Package

This package gives the next agent a compact entry point for the July 14 pickup.
It does not launch new jobs, mutate native CFD outputs, edit external Fluid, or
admit any new closure result.

## Files

- `source_manifest.csv`: evidence used for this handoff.
- `trusted_packages.csv`: documents/packages to open first by topic.
- `tomorrow_sequence.csv`: ordered next actions.
- `blockers_and_gates.csv`: current blockers and what would retire them.
- `launch_state.csv`: scheduler state and launch decision.
- `summary.json`: machine-readable snapshot.

## Main Decisions

- No duplicate corrected-Q job was launched. Corrected Salt-Q job `3293924` is
  still running and should be monitored, not duplicated.
- AGENT-305's Salt2 coarse thermal repair-smoke job `3294001` completed
  `0:0` in `00:02:41`; read AGENT-305 before using it to rebuild the thermal
  gate.
- Full Fluid forward-v0 `solve_case` confirmation is complete: job `3293960`
  ended `COMPLETED 0:0`, and the comparison package reports `6/6` pass rows.
- The next predictive-model work is hydraulic-first: apply/test the
  `H1_localized_named_loss_and_reset_bundle` candidate before any final
  forward-v1 or thermal-fit claim.
- AGENT-308 is active for a bounded H1 proxy screen; treat it as screen-only
  until its package/status closes.
- Thermal closure remains non-admitted: the fine reconstructed-temperature
  blocker is retired, but sign review, missing coarse thermal triplets, and
  downcomer policy still block UA/HTC/Nu fitting.
- The corrected Salt-Q terminal harvest should wait for job `3293924` to exit.

## Open Tomorrow

Start with the operational note:
`operational_notes/07-26/13/2026-07-13_TOMORROW_START_HERE.md`.
