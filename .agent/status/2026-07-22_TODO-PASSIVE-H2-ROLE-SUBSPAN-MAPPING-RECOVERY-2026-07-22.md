---
provenance:
  generated_by: tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py
  task_id: TODO-PASSIVE-H2-ROLE-SUBSPAN-MAPPING-RECOVERY-2026-07-22
tags: [status, PASSIVE-H2, patch-subspan, setup-UQ]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/source_family_patch_subspan_coverage.csv
---
# TODO-PASSIVE-H2-ROLE-SUBSPAN-MAPPING-RECOVERY-2026-07-22

## Objective

Use the thermal boundary patch-role table to recover patch/subspan coverage
for the five PASSIVE-H2 source families, decide Salt3/Salt4 diagnostic
runtime-smoke eligibility, and compute same-QOI setup-only UQ from existing
train-context sensitivity rows.

## Outcome

Decision: `passive_h2_role_subspan_mapping_recovered_diagnostic_uq_done_no_release_no_freeze`. Setup patch/subspan coverage is recovered
for `15/15`
case-family rows. Salt3 and Salt4 are eligible for a later diagnostic
runtime-smoke compute row, but protected scoring remains closed. Existing
setup perturbation deltas produce diagnostic same-QOI UQ for
`6/6`
labels. Release-ready source/property rows remain `0`,
freeze-ready candidates remain `0`, and no
final score is claimed.

## Changes Made

Built `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery` with patch/subspan coverage, Salt3/Salt4 runtime-smoke
eligibility, same-QOI setup-only UQ, release gates, next-action queue,
guardrails, source manifest, README, and summary artifacts. Added task-owned
builder/test files plus this status, journal, and import manifest.

## Validation

Validation commands run: builder, unit tests, py_compile, JSON parse,
runtime-input lint, split-policy lint, finish_task, repo-index check, and scoped
diff check.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, protected scoring, fitting/model selection,
source/property/Qwall/numeric heat-loss release, coefficient admission,
candidate freeze, final-score claim, S11/S12/S13/S15/S6 trigger, hidden
multiplier, residual absorption into internal Nu, or runtime-leakage
relaxation.
