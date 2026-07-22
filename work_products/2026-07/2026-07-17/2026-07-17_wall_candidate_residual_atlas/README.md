---
provenance:
  created_by: AGENT-520
  created_utc: 2026-07-17T21:05:08.064099+00:00
  source_packages:
    - work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization
    - work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate
    - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score
tags:
  - forward-predictive-model
  - wall-test-section
  - residual-atlas
  - freeze-blocker
related:
  - .agent/status/2026-07-17_AGENT-520.md
  - .agent/journal/2026-07-17/wall-candidate-residual-atlas.md
  - imports/2026-07-17_wall_candidate_residual_atlas.json
status: current
---

# Wall Candidate Residual Atlas

This package consolidates completed PB/WTD evidence and the current AGENT-511
heater-source state. It does not launch jobs or alter admission state.

## Result

- Completed candidate gate rows reviewed: `14`.
- Pending candidate gate rows reviewed: `1`.
- Probe residual rows available: `102`.
- Role/segment residual rows available: `60`.
- AGENT-511 state: `pending_or_live_no_completed_rows` with `0` completed coupled rows.
- Freeze status: `blocked`.

The current evidence says passive distribution and wall-temperature-drive
variants do not fix the temperature-shape failure. AGENT-511 cannot be used as
scientific failure evidence until its coupled rows land; while job `3300966` is
live/pending, the immediate action is to consume AGENT-511, not submit duplicate
heater-source work.

## Files To Open First

- `candidate_gate_matrix.csv`
- `probe_residual_atlas.csv`
- `role_segment_residual_rank.csv`
- `thermal_failure_mode_decision.csv`
- `next_candidate_decision.csv`
- `freeze_gate_status.csv`

## Guardrails

No native solver outputs, registry/admission state, Fluid source, or scheduler
state were mutated. Salt3/Salt4 remain score-only, and external/blind rows are
not used for fitting or model selection.
