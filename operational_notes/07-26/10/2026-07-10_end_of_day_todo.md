# 2026-07-10 End-of-Day TODO

Tags: #end-of-day #thermal-parity #live-job #corrected-q #salt1-nominal

## Related

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `operational_notes/07-26/10/2026-07-10_corrected_q_weekend_handoff.md`
- `operational_notes/07-26/10/2026-07-10_srun_tmux_allocation_dependency_handoff.md`
- `operational_notes/07-26/13/2026-07-13_live_job_heartbeat_and_cleanup_call.md`

## Start Here Next Meeting

- First open: `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`.
- Thermal roadmap: `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`.
- Operational live-job TODOs remain below.
- Documentation robustness pass: `AGENT-260` added lightweight `Related` blocks
  and tags to the thermal-parity note cluster.

Last scheduler refresh: `2026-07-10T17:23:00-0500`.

## Leave Running

- `3282992` Salt1 nominal continuation: still running on `c318-016`
  (`2-04:01:18` elapsed at last refresh); do not admit until terminal gate
  evidence exists.
- `3288671` selected corrected-Q packed continuation: keep monitoring. Salt1
  -10Q and Salt1 +10Q are running on `c318-017`; Salt4 +10Q failed after
  `00:02:33` and needs repair.
- `salt4_attach_3288671` tmux / attached `srun`: keep alive while attached
  Salt4 step `3288671.5` is running. See
  `operational_notes/07-26/10/2026-07-10_srun_tmux_allocation_dependency_handoff.md`.

## Do Not Submit Yet

- No bulk corrected-Q resubmit.
- No duplicate Salt2 pressure extraction.
- No Salt4 +10Q corrected resubmit until the OpenFOAM time-precision failure is
  repaired and preflighted.
- No closure refits from corrected-Q rows without explicit gate evidence.

## Submit/Run Next, After Preconditions

- Post-exit gate for Salt1 nominal once `3282992` exits.
- Post-exit gate for surviving selected corrected-Q Salt1 rows once `3288671`
  exits or those steps stop.
- Single-row Salt4 +10Q corrected continuation only after start-time /
  timePrecision/restart-name repair.
- Salt2 refined pressure-only mesh-family comparison and sign review from the
  completed AGENT-248 outputs.

## Durable Labels

- Salt1 nominal is a nominal endpoint candidate only after admission.
- Corrected-Q rows remain sensitivity/correlation-support.
- Thermal closure remains blocked by reconstructed-`T` repair; pressure-only
  outputs are useful but not thermal admission evidence.
