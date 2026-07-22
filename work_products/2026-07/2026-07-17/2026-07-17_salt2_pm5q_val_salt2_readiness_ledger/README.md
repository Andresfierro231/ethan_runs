---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_patch_heat_ledger.csv
tags: [fluid-walls, readiness-ledger, salt2-pm5q, val-salt2, external-test]
related:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/README.md
  - .agent/status/2026-07-17_AGENT-484.md
task: AGENT-484
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt2 +/-5Q and val_salt2 fluid+walls Readiness Ledger

## Start Here

Open `fluid_walls_readiness_ledger.csv` first. It is the row-by-row ledger for
`salt2_lo5q`, `salt2_hi5q`, and `val_salt2` across the steady-state
`fluid+walls` dimensions: geometry, material stack, pressure model, thermal
circuit, source/sink role, boundary-layer state, recirculation flags, and
uncertainty.

This package is existing-evidence-only. It did not submit jobs, repair native
case trees, edit registry state, or change scientific admission. It assembles
the current evidence into one comparable status contract for tomorrow's model
work.

## Main Result

- Cases reviewed: `3`.
- Readiness rows: `21`.
- Pressure rows: `18`.
- PM5/upcomer rows: `7`.
- Thermal source/sink rows: `26`.
- Fit-admitted pressure coefficient rows: `0`.
- Rows with admitted pressure model status: `0`.

Salt2 +/-5Q rows are holdout/testing-only. `val_salt2` is external-test-only.
None of these rows may be used for fitting, tuning, or model selection under
the AGENT-481 split policy.

## Files

- `case_inventory.csv`: case-level split role, legal use, representative time,
  terminal window, and evidence coverage.
- `fluid_walls_readiness_ledger.csv`: the main segment/branch readiness table.
- `thermal_source_sink_ledger.csv`: section heat/source/sink roles and sign
  convention.
- `pressure_readiness_ledger.csv`: pressure branch rows and admission blockers.
- `pm5_recirc_readiness_ledger.csv`: Salt2 +/-5Q PM5 repaired-field rows plus
  the explicit missing/queued `val_salt2` PM5 row.
- `uncertainty_and_admission_status.csv`: uncertainty blockers and fit/score
  implications.
- `source_manifest.csv`: all consumed source paths.
- `summary.json`: machine-readable counts and guardrail booleans.

## Interpretation

Geometry is mostly admitted because the segment map and model-form contract are
established. Material stack is still partial except for the bare-quartz test
section. Pressure is diagnostic for the 18 mapped branch rows: the harvested
ladders exist, but current pressure tables still admit zero true `f_D` or
component `K` fit rows. The three junction/stub rows are marked missing for
segment-local pressure because this package did not consume a junction-local
pressure/K artifact.

Thermal source/sink roles are present as realized CFD targets, not runtime model
inputs. Salt2 +/-5Q has section heat reduction and repaired PM5 wall-band fields.
`val_salt2` has a strong section/patch/junction heat ledger for external-test
scoring, but it does not yet have the same PM5/upcomer matched-plane evidence in
this source set.

## Do Not Do

- Do not fit or tune on `salt2_lo5q`, `salt2_hi5q`, or `val_salt2`.
- Do not promote diagnostic pressure rows into `f_D` or `K` coefficients.
- Do not treat realized `wallHeatFlux` or cooler duty as predictive runtime
  inputs.
- Do not infer `val_salt2` PM5/upcomer recirculation metrics from Salt2 +/-5Q.
- Do not submit duplicate pressure ladder jobs for these rows.

## Next Work

The shortest next step is a bounded F6/internal-Nu review for Salt2 +/-5Q using
the AGENT-406 repaired PM5 metrics, preserving holdout labels. A separate
optional follow-on can extract `val_salt2` PM5/upcomer fields on staged copies
if final external scoring requires matched-plane recirculation metrics.
