---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/README.md
  - operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md
tags: [TP2, sensor-map, forward-v1, validation-only]
related:
  - .agent/status/2026-07-16_AGENT-463.md
  - imports/2026-07-16_tp2_1d_model_evidence.json
task: AGENT-463
date: 2026-07-16
type: journal
status: complete
---
# TP2 1D Model Evidence

## Why This Exists

TP2 had already been restored in policy as a gated post-solve scoring target,
but the prior package left `TP2_finite_prediction_before_aggregate` pending.
This work converts that policy into durable evidence by running a bounded 1D
sensor replay with TP2 projected onto the bottom-right junction.

## What Changed

Added `tools/analyze/build_tp2_1d_model_evidence.py` and focused tests. The
builder writes a generated projected sensor registry under the work product,
preserving TP2's original provisional coordinate in provenance columns while
placing TP2 on the 1D bottom-horizontal/right-downcomer junction for scoring.

The Fluid source tree was used read-only. An active Fluid task owns solver
files, so this package intentionally avoids external source edits and performs
the projection in the Ethan evidence layer.

## Finding

TP2 now has `3/3` finite diagnostic 1D prediction rows in the bounded replay.
The current aggregate is `5 TP + 10 TW`; after TP2 gates pass it is
`6 TP + 10 TW`. The diagnostic RMSE changes from `163.588758922 K` to
`163.760647979 K`.

Admission status is intentionally conservative:

- TP2 restored sensor target: `validation-only`
- other scoreable TP/TW labels: `validation-only`
- consumed AGENT-360 replay rows: `diagnostic-only`
- TW10 shell surrogate: `blocked`
- final predictive forward-v1: `blocked`

## Guardrails

TP2 remains forbidden as a runtime temperature input, fit target, sensor-wise
correction, or closure-calibration row. Native CFD outputs, registry/admission
state, scheduler state, generated docs index files, and external Fluid source
files were not mutated.
