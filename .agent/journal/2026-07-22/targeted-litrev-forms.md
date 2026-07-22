---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/untried_litrev_model_forms.csv
  - operational_notes/maps/literature-synthesis-and-gates.md
tags: [literature-synthesis, model-forms, pressure, thermal, negative-k]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_targeted_litrev_forms/README.md
  - .agent/status/2026-07-22_TODO-TARGETED-LITREV-FORMS.md
  - imports/2026-07-22_targeted_litrev_forms.json
task: TODO-TARGETED-LITREV-FORMS
date: 2026-07-22
role: Writer/Implementer
type: journal
status: complete
supersedes: []
superseded_by:
---

# Targeted Litrev Forms

Task: `TODO-TARGETED-LITREV-FORMS`

## Attempted

I used the 2026-07-21 literature model-form extraction package, the 2026-07-13 untried literature forms table, and the living literature synthesis map to convert literature lessons into explicit candidate equation-family records. I kept the work document-only because the board row specifically forbids formula implementation until constants and primary-source definitions are verified.

## Observed

The literature set is strongest for methods and exclusions:

- NIST TN 2206 and Csizmadia/Hos support a pressure ledger with static/reduced pressure basis, kinetic and hydrostatic corrections, straight/developing subtraction, and recovery before any K value is interpreted.
- Shah/London and Shah references support a laminar straight/developing friction baseline, but only after Darcy/Fanning convention, reset distance, geometry, and pressure basis are verified.
- Muzychka/Yovanovich and Everts/Meyer-type sources support gated thermal-developing and mixed-convection forms, but the current package does not verify constants or full source-envelope overlap.
- VDI supports a heat-loss resistance network as setup accounting, not as a way to tune internal Nu.
- Exchange-cell and signed-flow literature supports architecture selection for recirculation, not universal coefficient transfer.

## Inferred

The negative lower-right corner component-K behavior is not a failed thesis path; it is usable evidence that the measured span should be treated as section-effective unless three conditions pass: reverse-flow gate, component isolation with valid straight/development subtraction, and same-QOI uncertainty. This directly supports the hybrid pressure route: an explicit throughflow-plus-recirculation pressure residual model is more defensible than hiding that behavior inside F6 or a universal component K.

## Contradictions Or Caveats

- Some literature gives compact coefficient forms, but the source domains do not yet match the TAMU geometry, pressure basis, property basis, or recirculation regime closely enough for admission.
- The strongest pressure sources improve bookkeeping and rejection criteria before they supply new tuned coefficients.
- The thermal literature can support a candidate inventory and regime map now, but not an internal Nu fit while source/sink and external heat-loss ownership remain unresolved.

## Next Useful Actions

1. Execute the no-fit hybrid pressure bakeoff against the section-effective residual and the F3 apparent reference.
2. Recover CAND001 terminal low-recirculation pressure anchors when the running scheduler job finishes.
3. Verify primary-source constants and definitions for the Shah/developing pressure reference before coding any formula.
4. Build a row-level nondimensional regime map for thermal closure eligibility.

Validation passed for JSON formatting, CSV parsing, runtime-input lint, source/property gate strict mode, split-policy lint, import-manifest JSON formatting, and final task handoff.
