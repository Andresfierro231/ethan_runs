---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/thesis_model_form_insert.md
tags: [mf12, bulk-to-tp, thermal-development, thesis-model-form]
related:
  - .agent/status/2026-07-22_TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/mf12-bulk-to-tp-formula-gate.md
  - imports/2026-07-22_mf12_bulk_to_tp_formula_gate.json
task: TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# MF12 Bulk-to-TP Formula Gate

## Why This Exists

The corrected model forms show that TP error can be compressed strongly before
TW error is addressed. MF12 asks whether that improvement can be represented as
a source-bounded model form instead of an empirical offset.

## Result

Decision: `diagnostic_only_needs_source_basis`.

The M3 train TP residual is uniformly cold across the five available Salt2 TP
rows, with mean signed error `-15.091423 K`. D2 improves transfer TP RMSE from
`13.5673279702 K` to `4.38159298515 K`. This supports a bulk-to-TP projection
model-form hypothesis.

MF12 writes the physically admissible family as:

```text
T_TP = T_bulk + sigma_q * A_source * Phi(Gz, x/D, reset, BC)
```

or, for source-placement memory:

```text
T_TP = T_bulk + integral_upstream W(reset,x) q_setup(s)/(mdot cp) dx
```

These forms are not ready for a smoke run. The source amplitude, source/property
labels, same-QOI TP projection UQ, and runtime wall/profile basis are not
released.

## Output Files

- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/thesis_model_form_insert.md`
- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/candidate_bulk_to_tp_formulas.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/formula_release_gap_matrix.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/next_study_queue.csv`

## Next Sequence

1. `signed_source_property_heat_path_release_preflight`
2. `same_qoi_tp_projection_uq`
3. `runtime_wall_profile_basis_for_tp_projection`
4. `train_only_mf12_formula_smoke_after_release`
5. `tw_after_tp_residual_ownership`

## Guardrails

No fitting, protected scoring, source/property release, coefficient admission,
Fluid solve, scheduler action, native-output mutation, or residual absorption
into internal Nu was performed. The failed `bash -n` check was a validation
operator error on Python files and was replaced by `python3.11 -m py_compile`.
