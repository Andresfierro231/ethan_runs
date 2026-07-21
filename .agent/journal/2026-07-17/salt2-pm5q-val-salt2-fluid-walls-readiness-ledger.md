---
provenance:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
tags: [fluid-walls, readiness-ledger, salt2-pm5q, val-salt2, external-test]
related:
  - .agent/status/2026-07-17_AGENT-484.md
  - imports/2026-07-17_salt2_pm5q_val_salt2_fluid_walls_readiness_ledger.json
task: AGENT-484
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Salt2 +/-5Q and val_salt2 fluid+walls Readiness Ledger

## Why This Exists

The July 16 `fluid+walls` model-form note asked for a row-by-row readiness
ledger carrying geometry, material stack, pressure model, thermal circuit,
source/sink role, boundary-layer state, recirculation flags, and uncertainty
status. The July 17 split policy makes Salt2 +/-5Q holdout/testing evidence and
`val_salt2` external-test evidence. This task assembled those rows into one
reproducible package from existing postprocessed evidence.

## What Was Built

The reusable builder consumes the canonical split policy, AGENT-406 Salt2 +/-5Q
PM5 repair outputs, pressure ladder admission/map outputs, the corrected-Q heat
role reduction, and the AGENT-422/483 `val_salt2` heat/admission outputs.

It writes:

- `case_inventory.csv`
- `fluid_walls_readiness_ledger.csv`
- `pressure_readiness_ledger.csv`
- `pm5_recirc_readiness_ledger.csv`
- `thermal_source_sink_ledger.csv`
- `uncertainty_and_admission_status.csv`
- `source_manifest.csv`
- `README.md`
- `summary.json`

## Findings

Geometry is mostly admitted for the mapped branches. Material stack is still
partial except for the bare-quartz test section. Pressure remains diagnostic for
the 18 mapped branch rows and missing for the three junction-local rows in this
package. No pressure `f_D` or `K` coefficient is admitted.

Salt2 +/-5Q PM5 field availability is repaired for upcomer inlet/mid/outlet and
wall-band `wallHeatFlux`, but F6/internal-Nu rows remain diagnostic and
holdout-only. `val_salt2` has heat and pressure ledgers suitable for external
test targets, but the package explicitly marks PM5/upcomer matched-plane
features as missing/queued rather than inferring them from Salt2 +/-5Q.

## Next Task Sequence

Open first:

1. `work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/fluid_walls_readiness_ledger.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/pm5_recirc_readiness_ledger.csv`

Recommended next work:

1. Run bounded F6/internal-Nu diagnostic review for Salt2 +/-5Q using AGENT-406
   repaired PM5 rows, preserving holdout/no-fit labels.
2. Decide whether final external scoring requires `val_salt2` PM5/upcomer
   extraction. If yes, create a separate staged-copy compute-node task.
3. After active AGENT-482 releases map/index ownership, cross-link this package
   from the relevant topic map and regenerate docs indexes.

## Guardrails

No native solver outputs, registry files, scheduler jobs, generated indexes, or
external Fluid files were changed. This package is an evidence ledger and does
not admit new scientific coefficients.
