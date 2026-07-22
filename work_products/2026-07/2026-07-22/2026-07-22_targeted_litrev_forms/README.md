---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/untried_litrev_model_forms.csv
  - operational_notes/maps/literature-synthesis-and-gates.md
tags: [literature-synthesis, model-forms, pressure, thermal, source-property-gate]
related:
  - .agent/status/2026-07-22_TODO-TARGETED-LITREV-FORMS.md
  - .agent/journal/2026-07-22/targeted-litrev-forms.md
  - imports/2026-07-22_targeted_litrev_forms.json
task: TODO-TARGETED-LITREV-FORMS
date: 2026-07-22
role: Writer/Implementer
type: work_product
status: complete
supersedes: []
superseded_by:
---

# Targeted Literature Model Forms

Task: `TODO-TARGETED-LITREV-FORMS`

Decision: `targeted_litrev_forms_ready_no_formula_implementation_no_admission`.

This package converts the targeted literature review into gated model-form records. It does not tune coefficients, implement formulas, admit a predictive closure, or use diagnostic two-tap corner rows as F6 fit evidence.

## Outputs

- `source_manifest.csv`: source and provenance ledger.
- `candidate_equation_forms.csv`: candidate equation families, required inputs, nondimensional groups, branch applicability, validity constraints, and source/property labels.
- `exclusion_criteria.csv`: explicit rejection rules for component K, friction, thermal, heat-loss, transient, and ROM candidates.
- `implementation_readiness_gate.csv`: evidence needed before formulas can be implemented or used in thesis scoring.
- `source_overlap_and_validity_matrix.csv`: TAMU overlap assessment by literature source.
- `next_task_queue.csv`: follow-up rows that can unblock implementation without fitting present diagnostic residuals.
- `summary.json`: machine-readable decision summary.

## Result

The literature supports a thesis-useful model-form map, not immediate coefficient admission. The strongest near-term lanes are:

- Section-effective pressure modeling with explicit throughflow plus recirculation terms.
- Straight/developing laminar pressure reference and reset-distance bookkeeping before any F6 correction.
- Recirculating-upcomer exchange-cell thermal architecture after same-QOI evidence improves.
- Setup-only heat-loss resistance network work that remains separate from internal Nu fitting.

The negative component-K result remains publishable: the failed corner two-tap rows show why a universal fitting loss is not supported without reverse-flow gates, valid isolation/subtraction, and same-QOI UQ. They should be presented as diagnostic evidence motivating the hybrid pressure model, not as fit rows.

## Guardrails

- No native solver outputs were edited.
- No registry or admission state was changed.
- No scheduler action was taken.
- No Fluid or thesis LaTeX files were edited.
- All forms remain `no_fit_no_admission` until constants, pressure basis, property labels, validity ranges, and branch gates are row-specific and verified from primary sources.
