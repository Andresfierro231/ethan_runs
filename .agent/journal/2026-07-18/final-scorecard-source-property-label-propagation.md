---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/source_property_label_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/final_scorecard_case_coverage_audit.csv
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
tags: [forward-model, final-scorecard, source-envelope, property-sensitivity]
related:
  - .agent/status/2026-07-18_TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS.md
  - imports/2026-07-18_final_scorecard_source_property_label_propagation.json
task: TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS
date: 2026-07-18
role: Forward-pred/Literature-synthesis/Implementer/Tester/Writer
type: journal
status: complete
---
# Final Scorecard Source/Property Label Propagation

Task: TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS

## Attempted

Implemented the requested source/property label propagation on the first real
scorecard surface named by AGENT-538: the final predictive scorecard shell.
This was a schema and guardrail update only.

## Observed

AGENT-538 marks the final predictive `prediction_join_shell.csv` as
`missing_labels` and requires source-validity envelope and property-mode
sensitivity labels before future scorecards report fit/admission rows.

The AGENT-538 coverage audit has row-specific labels for
`salt2_jin_nominal`, `salt3_jin_nominal`, and `salt4_nominal`, but not for
Salt1, perturbation, external, or future rows. Those gaps are blockers, not
permission to infer source overlap or property independence.

After regeneration, `case_partition_contract.csv` has 16 labeled rows and
`prediction_join_shell.csv` has 79 labeled rows. The new
`source_property_label_gate_audit.csv` reports zero missing-label rows and zero
rows that allow fit/model selection despite missing source/property coverage.

## Inferred

The correct implementation is to preserve split intent separately from final
fit permission. `split_fit_allowed` and `split_model_selection_allowed` still
show the canonical split policy, while `fit_allowed` and
`model_selection_allowed` are now gated by AGENT-538 source/property coverage.
That leaves Salt2/Salt3/Salt4 nominal available for future fit/model-selection
language, while Salt1 remains train-partitioned but blocked pending refresh.

## Contradictions And Caveats

This update does not create a final freeze, score a model, admit a candidate,
or decide a property lane. It carries the current AGENT-538 preferred label
mode `jin_viscosity_parida_cp_santini_k` for the available nominal rows and
uses explicit blocked labels for missing-coverage rows.

## Next Useful Actions

Refresh source-envelope/property labels for Salt1 before any final Salt1-4
fit/freeze claim. Apply the same label-gate pattern to the next segment
pressure, segment thermal, F6, or TSWFC/UMX scorecard builder before those
packages report fit/admission language.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, reports/thesis files, fitting,
tuning, model selection, or scientific admission state were mutated.
