---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/next_study_queue.csv
tags: [operational-note, mf14, same-qoi, predictive-model]
related:
  - operational_notes/07-26/22/2026-07-22_MF13_SIGNED_SOURCE_PROPERTY_HEAT_PATH_RELEASE_PREFLIGHT.md
  - .agent/status/2026-07-22_TODO-MF14-SAME-QOI-TP-PROJECTION-UQ-GATE-2026-07-22.md
task: TODO-MF14-SAME-QOI-TP-PROJECTION-UQ-GATE-2026-07-22
date: 2026-07-22
role: Sensor-map / Uncertainty / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# MF14 Same-QOI TP Projection UQ Gate

## Why This Exists

MF13 left signed source/property inputs closed. MF14 addresses the independent
projection question: even with source terms, a predictive model cannot claim TP
temperature agreement unless the TP projection from 1D bulk state to sensor QOI
has a runtime-legality and uncertainty boundary.

## Open First

- `work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/tp_same_qoi_projection_uq.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/projection_release_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/d2_reuse_boundary.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/next_study_queue.csv`

## Trusted Packages

- N4 sensor/QOI projection uncertainty table.
- 1D sensor projection operator TP/TW/wall/bulk package.
- D2 TP/TW QOI projection gate.
- MF13 signed source/property heat-path preflight.

## Result

Decision: `same_qoi_tp_projection_uq_fail_closed_no_runtime_temperature_release`.

TP1-TP6 all have same-QOI bulk-fluid projection labels, but zero rows have
quantitative same-QOI projection UQ, runtime temperature release, or a released
bulk-to-TP correction.

## Output Contract

MF14 is a projection/UQ gate. It does not perform new validation/holdout/external
scoring and does not admit D2 as a correction. D2 metrics are read-only
diagnostic context.

## Next Task Sequence

1. `runtime_wall_profile_basis_for_tp_projection`
2. `source_property_label_release_candidate_after_exact_fields`
3. `train_only_mf12_formula_smoke_after_release`
4. `tw_after_tp_residual_ownership`

## Do Not Do

Do not use TP sensor temperatures as runtime inputs. Do not use D2 offsets as
hidden corrections. Do not claim final predictive temperature agreement from
post-solve projection labels. Do not run MF12 formula smoke until projection,
source/property, and wall/profile gates pass.
