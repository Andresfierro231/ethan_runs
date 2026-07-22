---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/summary.json
tags: [d2, tp, tw, thermal-development, journal]
related:
  - .agent/status/2026-07-22_TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22.md
task: TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22
date: 2026-07-22
role: Sensor-map / Uncertainty / Thermal-modeling / Tester / Writer / Reviewer
type: journal
status: complete
---
# MF-D2 TP/TW QOI Projection Gate

## Attempted

The user clarified that the intended analysis sequence is TP first, then TW:
if TP is corrected as a bulk/fluid projection problem, TW can then be used to
study wall/boundary response. I claimed the existing D2 row and built an
evidence-only package to test whether the thermal-development path has promise.

## Observed

D2 is the separate TP/TW offset diagnostic from the suggested model-form tests.
It was trained only on Salt2 train-candidate residuals and reported on Salt3 and
Salt4 transfer rows. It improves transfer TP RMSE from `13.5673279702 K` to
`4.38159298515 K`, and transfer TW RMSE from `18.980361511 K` to
`12.5130610954 K`.

The N4 projection package maps TP rows as post-solve score targets only. The
LitRev developing-flow package contains reset-distance, Re/Pr/Gz, and branch
precheck evidence, but no admitted coefficient or released QOI projection
correction.

## Inferred

The evidence supports the thermal-development path as a promising diagnostic
route. The most defensible interpretation is layered:

1. TP is a bulk/fluid-state projection problem first.
2. Thermal development may explain a local probe-vs-bulk offset.
3. TW should be analyzed after the TP projection layer is bounded.
4. Remaining TW residual then belongs to wall/boundary/source-placement physics,
   not to an undifferentiated global temperature correction.

## Caveats

D2 is empirical and not source-bounded. It cannot be used as a correction,
runtime input, final score, coefficient, or admission evidence. The existing
thermal-development evidence is a precheck; it still lacks thermal reset
status, wall/core profile extraction, same-QOI uncertainty, and source/property
labels.

## Next Useful Actions

Run the next analysis in this order: bulk-to-TP existence proof, TP residual by
reset/Graetz coordinate, S13 wall/core/TP bridge, and TW residual after TP
projection.
