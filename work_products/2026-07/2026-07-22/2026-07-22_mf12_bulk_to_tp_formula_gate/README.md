---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/summary.json
tags: [mf12, bulk-to-tp, formula-gate, diagnostic-only]
task: TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# MF12 Bulk-to-TP Formula Gate

Decision: `diagnostic_only_needs_source_basis`.

MF12 tests whether the D2/MF07 bulk-to-TP signal can be converted into a
source-bounded model form. The answer is: not yet. A formula family can be
written, and the direction is scientifically plausible, but the release gates
fail closed because source/property labels, same-QOI TP projection UQ, and a
runtime wall/profile basis are missing.

Key results:

- candidate formula rows: `4`
- sensor evidence rows: `10`
- release gate rows: `6`
- M3 train TP mean signed error: `-15.091423 K`
- M3 transfer TP RMSE: `13.5673279702 K`
- D2 transfer TP RMSE: `4.38159298515 K`
- train-only smoke ready: `False`

## Files

- `candidate_bulk_to_tp_formulas.csv`
- `sensor_formula_evidence.csv`
- `formula_release_gap_matrix.csv`
- `next_study_queue.csv`
- `thesis_model_form_insert.md`
- `formula_provenance_compact.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No fitting, protected scoring, source/property release, coefficient admission,
Fluid solve, scheduler action, native-output mutation, or residual absorption
into internal Nu was performed.
