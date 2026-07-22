---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/same_qoi_uq_admission_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/matched_plane_recirc_field_harvest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_geometry_source_gap_recovery/geometry_source_gap_recovery.csv
tags: [pressure-ledger, minor-loss, source-envelope, recirculation, same-qoi-uq]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/README.md
task: TODO-PRESSURE-CORNER-COMPARISON-ADMISSION-REVIEW
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: work_product
status: complete
---

# Pressure Corner Comparison Admission Review

## Why This Package Exists

This package compares the frozen July 21 pressure-corner result against the
later LitRev-derived pressure-basis, recirculation, source-envelope, and same-QOI
uncertainty evidence. It decides only what label each current row may carry in
the 1D model evidence ledger.

## Open First

1. `pressure_corner_model_use_decision.json`
2. `pressure_corner_comparison_matrix.csv`
3. `pressure_corner_gate_review.csv`
4. `publication_delta_note.md`

## Output Contract

- `pressure_corner_comparison_matrix.csv` preserves the three frozen
  `corner_lower_right` rows and adds the post-review allowed label.
- `pressure_corner_gate_review.csv` records the eight required component-`K`
  gates per row.
- `pressure_corner_model_use_decision.json` records the model-use decision and
  explicit no-admission counts.
- `publication_delta_note.md` is the human-readable delta from the freeze.
- `source_manifest.csv` records read-only inputs.
- `summary.json` records row counts and guardrails.

## Results And Analysis

The review confirms the publication freeze. All three Salt2/Salt3/Salt4
`corner_lower_right` rows remain `section_effective` pressure-residual /
pressure-recovery diagnostics.

Observed facts:

- Gross static pressure rises are finite and hydrostatic dominated.
- Corrected available residuals are negative.
- Endpoint reverse-flow metrics are material, with reverse-area fraction near
  `0.763` and reverse-mass fraction near `0.5`.
- Same-QOI mesh/time uncertainty remains missing.
- The lower-right corner source envelope still lacks geometry/source fields
  required for ordinary component isolation.

Inferred interpretation:

- The rows can support discussion of hydrostatic domination, pressure recovery,
  recirculating section residuals, and the need for an ordinary low-reverse
  anchor.
- They cannot support a component `K`, cluster `K`, F6 fit, clipped negative
  coefficient, or hidden global multiplier.

## Do-Not-Do Guardrails

No native CFD/OpenFOAM outputs were mutated. No registry or admission state was
changed. No scheduler action, solver launch, postprocessing launch, Fluid edit,
external edit, fitting, tuning, model selection, F6 fit, component-`K`
admission, cluster-`K` admission, clipped `K`, or hidden global multiplier was
performed.
