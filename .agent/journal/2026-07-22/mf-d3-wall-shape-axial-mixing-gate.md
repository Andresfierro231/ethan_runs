---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/wall_shape_case_summary.csv
tags: [model-form, d3, wall-shape, axial-mixing, same-qoi, thesis]
related:
  - .agent/status/2026-07-22_TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22.md
  - imports/2026-07-22_mf_d3_wall_shape_axial_mixing_gate.json
task: TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal: D3 Wall-Shape / Axial-Mixing Gate

## Attempted

Computed the D3 wall-index residual decomposition and crosswalked the result to
S12 exchange evidence, S13 target/minus/plus same-QOI triplets, and N4 sensor
projection bounds.

## Observed

D3 improves the wall-temperature residual shape. Salt3 TW RMSE moves from
`19.3315846151 K` to `9.33875871489 K`; Salt4 TW RMSE moves from
`18.6225154705 K` to `10.2317345598 K`. The M3 wall-index slope is about
`2.49-2.65 K/index` on transfer rows, while D3 leaves slopes near
`0.11-0.26 K/index`.

S13 has four same-QOI triplet-ready labels, but UQ is `ready_not_executed` and
production use is still false. N4 supports using TW rows as bounded post-solve
score targets, not runtime inputs.

## Inferred

D3 is useful evidence that residual shape is organized, not random. The most
promising physical follow-up remains wall/core exchange or axial-mixing
evidence, but the admission gate is blocked by same-QOI UQ, production harvest,
source/property release, and lack of independent source-bounded coefficient.

## Caveats

D3 is residual-trained from Salt2. It is not a runtime model form, not a
source-bounded heat-path closure, and not a final validation score.

## Next Useful Actions

1. Claim a same-QOI UQ execution row for the now triplet-ready S13 labels.
2. Use the D3 wall-shape decomposition as context for any later S12/S13
   thermal-shape candidate.
3. Continue to D2 TP/TW projection gate if the next work remains diagnostic.
