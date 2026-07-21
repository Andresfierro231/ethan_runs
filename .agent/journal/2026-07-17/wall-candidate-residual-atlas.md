---
provenance:
  created_by: AGENT-520
  created_utc: 2026-07-17T21:05:30Z
task: AGENT-520
tags:
  - forward-predictive-model
  - wall-test-section
  - residual-atlas
  - scientific-review
related:
  - .agent/status/2026-07-17_AGENT-520.md
  - imports/2026-07-17_wall_candidate_residual_atlas.json
  - work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/README.md
status: current
---

# Wall Candidate Residual Atlas

## Why This Avenue Exists

AGENT-515 showed that PB2/PB3 wall distribution candidates improve mdot but
worsen all-probe/TW errors. AGENT-513 then showed that wall-temperature-drive
variants also fail: WTD1 repeats the mdot/temperature tradeoff and WTD2 is worse
in both mdot and temperature. AGENT-511 is the planned heater-source
redistribution lane, but at atlas build time its package still had no completed
coupled rows and Slurm job `3300966` was live.

This package prevents the next agent from drawing premature conclusions from
AGENT-511 while still using the completed AGENT-513 per-probe evidence to
localize the current thermal-shape failure.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/candidate_gate_matrix.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/probe_residual_atlas.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/role_segment_residual_rank.csv`
5. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas/next_candidate_decision.csv`

## Observed Output

- `candidate_gate_matrix.csv` contains 14 completed PB/WTD gate rows plus one
  pending AGENT-511 row.
- `probe_residual_atlas.csv` contains 102 AGENT-513 probe residual rows.
- `role_segment_residual_rank.csv` contains 60 AGENT-513 grouped residual rows.
- `thermal_failure_mode_decision.csv` labels PB1/PB2/PB3 passive/static
  distribution as not sufficient, WTD1 drive as not sufficient, WTD2 as wrong
  direction, and AGENT-511 as pending.
- `freeze_gate_status.csv` keeps `freeze_blocked_no_wall_candidate_admitted`
  blocked.

## Inferred Interpretation

The completed evidence has now ruled out passive-total heat scaling, Salt2-shape
passive distribution, and wall-temperature drive selector changes as sufficient
standalone repairs. AGENT-511 must still be completed before rejecting heater
source redistribution. If AGENT-511 also fails after completed coupled rows, the
next physics candidate should be explicit test-section wall/fluid coupling
before a broader junction/axial mixing proxy.

## Contradictions Or Caveats

- AGENT-511 is not a completed scientific result yet. Its current package
  contains 21 pending grid rows and no coupled deltas.
- AGENT-513 has strong probe-level residual evidence, but it is specific to
  wall-temperature-drive candidates, not to heater-source redistribution.
- The atlas did not submit, cancel, or harvest any scheduler job.

## Next Useful Actions

1. Continue monitoring Slurm job `3300966` for AGENT-511.
2. When it exits, rerun/close AGENT-511 and regenerate this atlas so HS1 is
   classified from completed evidence.
3. If HS1 fails completed gates, claim a new explicit test-section wall/fluid
   coupling candidate package.
4. Keep corrected freeze blocked until validation and holdout mdot/all-probe/TW
   gates pass.

## Do-Not-Do Guardrails

- Do not submit duplicate heater-source or PB/WTD jobs while AGENT-511 is live.
- Do not treat AGENT-511 pending rows as failed scientific evidence.
- Do not use `val_salt2`, Salt2 +/-Q, PM10, future CFD, or new CFD for model
  selection.
- Do not use realized CFD `wallHeatFlux` as a runtime predictive input.

## Validation

- `python3 -m py_compile tools/analyze/build_wall_candidate_residual_atlas.py tools/analyze/test_wall_candidate_residual_atlas.py`
- `python3 tools/analyze/build_wall_candidate_residual_atlas.py`
- `python3 -m unittest tools.analyze.test_wall_candidate_residual_atlas`
