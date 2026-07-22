---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/summary.json
tags: [thesis, model-form-scoreboard, signed-error-shape, no-admission]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22.md
  - imports/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch.json
task: TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer / Coordinator
type: journal
status: complete
---
# Thesis Scoreboard Signed-Error Shape And Model-Form Dispatch

Task: `TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22`

## Attempted

I claimed a narrow scoreboard enrichment row and implemented a reproducible
builder that consumes the completed thesis master model-form scoreboard plus
the newest S13, thermal residual, and pressure/F6 gate summaries. The work did
not run new scoring, fitting, solver, sampler, harvest, or UQ jobs.

## Observed

The signed-error shape study shows that M3 is the best current legacy numeric
comparator, but it is still cold. Model-level mean group RMSE values are:

- M1: `158.48476999311254 K`
- M1b: `152.10477089894718 K`
- M2: `26.181478391088774 K`
- M3: `16.94570103203358 K`

M3's mean signed group bias is `-14.656241771806632 K`, and its local shape RMSE
after removing that bias is `7.885223080969407 K`. The M3 TW rows for Salt3 and
Salt4 are classified as mixed-sign local-shape dominated after bias removal,
which means a pure global offset would not fully repair the wall-temperature
shape.

The S13 same-QOI status has improved relative to the first fail-closed gate
because target-minus rows now exist, but target-plus rows remain `0` and
same-QOI-ready labels remain `0`.

## Inferred

The next plausible error-reduction paths are not arbitrary coefficient fits.
They are the physical owners already named by the gates:

1. M0 setup-only baseline, to establish the lower-bound reference.
2. M5/MF-04 upcomer exchange, if target-plus and same-QOI UQ can be recovered.
3. M2+ passive wall/test-section source-bounded repair, because M2/M3 remain
   systematically cold.
4. MF-02 pressure/mdot coupling, because mdot changes can move the thermal
   level but lower-right pressure remains diagnostic only.

## Contradictions Or Caveats

The scoreboard figures are thesis-ready, but they remain legacy numeric context
for M1-M3 rather than final locked-split prediction scores. The M0 row is a gap
contract, not a baseline score. The S13 status is also not an admission: direct
Qwall evidence exists, target-minus evidence now exists, but target-plus and
same-QOI UQ remain missing.

## Next Useful Actions

1. Claim `TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22` to
   produce the real setup-only lower-bound predictions or an explicit
   missing-prediction matrix.
2. Claim `TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22`
   if the goal is to reduce the cold thermal bias physically.
3. Claim `TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22` if the goal
   is to quantify whether pressure/mdot changes can move the TP/TW level.
4. Keep S13 production harvest blocked until target-plus and mesh/GCI or
   same-QOI uncertainty evidence exists.
