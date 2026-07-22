# MF13 Signed Source/Property Heat-Path Release Preflight

This package performs the first MF12 follow-on study. It consumes existing diagnostic/source-contract evidence and asks whether signed heat-path inputs can be used by MF12 candidate formulas.

## Decision

`signed_source_property_release_preflight_fail_closed`

No source/property input is released here. No Fluid solve, fitting, protected split scoring, model selection, repair, admission, or final score was performed.

## Outputs

- `signed_heat_path_release_preflight.csv`: family-level release/fail-closed decision.
- `case_split_source_values.csv`: setup source/sink values with train/support versus protected split use separated.
- `source_property_release_gate.csv`: strict gate matrix.
- `mf12_formula_input_readiness.csv`: MF12 input readiness by formula and requirement.
- `thesis_heat_path_preflight_insert.md`: thesis-ready diagnostic paragraph.
- `next_study_queue.csv`: ordered continuation sequence.
- `source_manifest.csv` and `no_mutation_guardrails.csv`: provenance and mutation boundary.

## Claim Boundary

The study supports only a train/support diagnostic claim: signed source/sink metadata is useful for hypothesis design, but not yet a runtime predictive input. Validation, holdout, and external-test rows are not used for scoring or model selection.
