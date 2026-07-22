---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_d2_holdout_validation_disposition/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/candidate_bulk_to_tp_formulas.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/split_claim_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/summary.json
tags: [journal, d2, bulk-to-tp, protected-score-gate]
related:
  - .agent/status/2026-07-22_TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22.md
  - imports/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate.json
task: TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Writer / Reviewer / Tester
type: journal
status: complete
---
# D2 Source-Bounded Projection Holdout/External Score Gate

## Attempted

Claimed a narrow D2 protected-score gate row and reviewed the completed D2
disposition, MF12 formula gate, MF14 split/UQ gate, model-form training roster,
source/property/cp preflight, and TW-after-TP residual ownership package.

## Observed

D2 has promising diagnostic transfer evidence, including a transfer RMSE
improvement from `17.3645293096 K` to `10.5253939442 K`, and TP transfer RMSE
improvement from `13.5673279702 K` to `4.38159298515 K`.

MF14 records no validation, holdout, or external-test scoring. The training
roster states that validation/holdout scoring is locked because no frozen
candidate exists. The source/property/cp preflight records `cp_J_kg_K` and
property-mode release as not ready.

MF12 identifies the physical successors: signed Graetz/probe offset, signed
source integral/reset memory, and wall-profile projection. The downstream
wall-core and recirculation-exchange families remain useful after TP projection,
but they are blocked by wall/profile, Qwall/source, mesh/GCI, and production
harvest gates.

## Inferred

D2 should not be run on holdout or external-test data. It is an empirical
diagnostic residual shape, not a source-bounded predictive operator. The correct
progress path is to build a source-bounded D2 successor, freeze it from
train/support only, and then score protected rows once.

## Contradictions Or Caveats

The word "transfer" in prior D2 packets can be misread as protected validation.
This packet records that it is diagnostic transfer context, not a frozen
validation/holdout/external-test score.

## Files Changed

- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/**`
- `.agent/status/2026-07-22_TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22.md`
- `.agent/journal/2026-07-22/d2-source-bounded-projection-holdout-external-score-gate.md`
- `imports/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate.json`
- `.agent/BOARD.md`

## Commands Run

- `rg -n "TODO-D2|D2-HOLDOUT|D2_" .agent/BOARD.md`
- `head` on MF12, MF14, training roster, and source/property evidence CSVs.
- CSV/JSON parse check for the new package.
- `python3.11 tools/agent/finish_task.py --task-id TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22`

## Next Useful Actions

Use `projection_model_family_table.csv` as the shortlist. The best next science
row is a train/support-only MF12 source-bounded candidate freeze preflight:
release candidate-specific `cp_J_kg_K`, legal source/sink signs/magnitudes,
reset/Graetz state, and same-QOI TP UQ. Protected scoring remains closed until
that freeze exists.
