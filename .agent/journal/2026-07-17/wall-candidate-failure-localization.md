---
provenance:
  created_by: AGENT-515
  created_utc: 2026-07-17T21:48:45Z
task: AGENT-515
tags:
  - forward-predictive-model
  - wall-test-section
  - corrected-freeze
  - provenance
related:
  - .agent/status/2026-07-17_AGENT-515.md
  - imports/2026-07-17_wall_candidate_failure_localization.json
  - work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/README.md
status: current
---

# Wall Candidate Failure Localization

## Why This Avenue Exists

`val_salt2` and final predictive scoring remain blocked by
`freeze_blocked_no_wall_candidate_admitted`. AGENT-498 completed the July 17
pressure/wall/test-section distribution ladder and found no admitted candidate.
This pass converts that result into a reusable, audited failure-localization
package so the next agent does not submit duplicate PB1/PB2/PB3 jobs.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/wall_candidate_gate_failure_matrix.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/segment_heat_placement_failure_modes.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/probe_localization_data_gap.csv`
5. `work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/next_candidate_ladder.csv`

## Observed Output

AGENT-498 wall/test-section distribution candidates:

- 4 candidates reviewed.
- 8 validation/holdout coupled-delta rows reviewed.
- 8/8 rows improve mdot versus M3.
- 8/8 rows worsen all-probe and TW errors versus M3.
- 0/4 candidates admitted.

Segment heat placement:

- 36 rows reviewed.
- Held-out PB2/PB3 show upcomer/test-section loss underprediction.
- Junction and downcomer roles absorb excess loss in the held-out cases.
- This supports a source-placement, drive-temperature, axial-exchange, or
  junction-ownership failure mode.

Probe localization:

- `probe_delta_vs_m3.csv`, `probe_error_localization.csv`, and
  `role_segment_error_summary.csv` are populated with `136`, `204`, and `80`
  detail rows respectively.
- Sensor-level TP/TW attribution is defensible as held-out diagnosis from
  AGENT-498, while admission and tuning remain governed by the predeclared
  aggregate gates.

## Inferred Interpretation

The current wall candidates reduce the flow error but worsen the temperature
shape. That rules out a simple "admit it and freeze" path. The failure is not
runtime leakage because setup-only/runtime audits pass. The likely failure class
is that the 1D model places heat loss in the wrong spatial or physical bucket:
wrong wall-temperature drive, wrong heater/source redistribution, missing axial
mixing, or inadequate junction/stub ownership.

## Contradictions Or Limits

- PB2/PB3 AGENT-498 delta tables do not provide TP deltas versus M3; only
  all-probe and TW deltas are available. Candidate TP/TW/all-probe RMSE values
  remain available in `coupled_scorecard.csv`.
- Per-probe localization is available for held-out diagnosis, but it must not be
  used to tune or select candidates on Salt3/Salt4.
- AGENT-511 and AGENT-513 are active implementation rows; this package only
  cites them as downstream/related and does not edit their scopes.

## Next Task Sequence

1. Consume AGENT-513 wall-temperature-drive and AGENT-511 heater-source
   redistribution results together with this localization package.
2. Compare the newly completed AGENT-511/513 probe residuals against AGENT-498
   sensor-level failure modes.
3. If no candidate passes, test a junction-aware or axial-mixing proxy with
   split-clean admission gates.
4. Build the corrected freeze only after a wall/test-section candidate is
   admitted on the predeclared validation and holdout gates.

## Do-Not-Do Guardrails

- Do not submit duplicate PB1/PB2/PB3 coupled jobs.
- Do not use `val_salt2`, Salt2 +/-5Q, PM10, future +/-10Q, or new CFD for
  model selection.
- Do not mutate native solver outputs, registry/admission state, Fluid source,
  or active AGENT-514 scopes.
- Do not treat realized CFD `wallHeatFlux` as a runtime predictive input.

## Verification

- `python3 -m py_compile tools/analyze/build_wall_candidate_failure_localization.py tools/analyze/test_wall_candidate_failure_localization.py`
- `python3 tools/analyze/build_wall_candidate_failure_localization.py`
- `python3 -m unittest tools.analyze.test_wall_candidate_failure_localization`
