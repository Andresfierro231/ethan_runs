---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/matched_plane_recirc_field_harvest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/same_qoi_uq_admission_table.csv
  - .agent/BLOCKERS.md
tags: [recirculation, switching-calibration, thermal-closure, pressure-ledger]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/README.md
task: TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION
date: 2026-07-21
role: Hydraulics / Thermal-modeling / Writer
type: work_product
status: complete
---

# LitRev Recirculation Switching Calibration

## Why This Package Exists

The LitRev requires recirculation and recovery switches to be TAMU calibrated,
not copied from universal literature thresholds. This package defines the
calibration template and evidence needs for `F_A`, `F_m`, secondary flow,
stratification, velocity recovery, and pressure-gradient recovery.

## Open First

1. `switching_calibration_template.csv`
2. `unresolved_threshold_fields.csv`
3. `switching_training_split_requirements.csv`
4. `summary.json`

## Results And Analysis

Observed facts:

- The LitRev extraction defines `F_A`, `F_m`, secondary-flow intensity, and
  recovery diagnostics as required CFD postprocessing fields.
- Current lower-right pressure-corner endpoint rows have material reverse-flow
  metrics and are already blocked from ordinary `K`/F6 use.
- Upcomer rows are partly proxy, parse-incomplete, or missing wall-core thermal
  and coherent-cell fields.
- Same-QOI uncertainty is still missing for candidate threshold families.

Inferred interpretation:

- Current evidence can define switch inputs and conservative blocking logic.
- It cannot select final epsilon values for TAMU because the split, plane
  definitions, uncertainty, source-envelope labels, and held-out tests are not
  complete.

## Output Contract

- `switching_calibration_template.csv` defines each switching field, required
  basis, split discipline, false-negative rule, unresolved epsilon field, and
  current action.
- `switching_training_split_requirements.csv` separates train/support,
  development validation, holdout, and external-test use.
- `unresolved_threshold_fields.csv` lists why each epsilon remains unresolved.
- `source_manifest.csv` records read-only evidence.
- `summary.json` records row counts and guardrails.

## Do-Not-Do Guardrails

Do not import universal thresholds from literature. Do not change admission
state. Do not fit coefficients, select models, edit Fluid, launch solvers,
launch postprocessing, mutate native CFD outputs, mutate registry/admission
state, edit blockers, or refresh generated indexes from this package.
