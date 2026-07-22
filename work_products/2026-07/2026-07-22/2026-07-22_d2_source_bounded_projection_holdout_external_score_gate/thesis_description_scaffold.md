---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/candidate_bulk_to_tp_formulas.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/d2_score_improvement_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/split_claim_matrix.csv
tags: [thesis-methodology, bulk-to-tp, sensor-projection, thermal-development]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/README.md
task: TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22
date: 2026-07-22
role: Writer / Thermal-modeling
type: work_product
status: complete
---
# Thesis Scaffold: Bulk-to-TP / Sensor-Kind Projection

The segment model evolves a bulk, mixed-cup fluid temperature. The CFD and
experimental comparison targets include local sensor-kind quantities, such as a
thermocouple-plane or wall-proximate temperature. These are not automatically
identical to the segment bulk temperature when the thermal field is developing,
when a boundary condition changes along the loop, or when wall/core contrast is
large.

The diagnostic D2 result is used only to motivate this projection problem. D2
showed that a reduced residual shape can substantially reduce transfer error,
but its empirical offsets do not identify the physical heat path and are not
runtime-legal inputs. Therefore the predictive model must replace D2 with a
source-bounded projection operator.

A defensible projection operator should be described in boundary-layer and
development-layer terms:

- `MF12a` treats the probe offset as a signed thermal-development effect. The
  source sign determines whether the local boundary layer tends to heat or cool
  the sampled location relative to the segment bulk. The Graetz/reset coordinate
  controls how much of that source imprint remains at the sensor.
- `MF12b` treats the offset as an upstream source-memory effect. Heater power,
  cooler removal, passive wall loss, and test-section source terms contribute
  through legal source lanes and decay or reset with distance and mixing.
- `MF12c` treats the offset as a wall/core profile sampling effect. The probe
  reads a location in a radial or near-wall profile, so the model must predict
  wall/core contrast before projecting to the sensor-kind target.
- `MF15` and `M5/MF04` become relevant when the remaining error after TP
  projection is tied to wall/core exchange or recirculating upcomer exchange
  rather than a single-stream internal Nusselt number.

The methodology guardrail is that missing heat is not absorbed into internal
`Nu`. Internal convection, wall conduction, source/sink ownership, passive
external loss, radiation, storage, sensor projection, and residual are separate
lanes. A correction can be tested on protected data only after one runtime-legal
candidate is frozen from train/support data, with coefficients and inputs fixed.
