---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_strict_row_specific_source_envelope_recovery/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/row_level_release_candidate_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/formula_release_gap_matrix.csv
tags: [journal, source-property, source-envelope, s13, mf12]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_strict_row_specific_source_envelope_recovery/README.md
  - .agent/status/2026-07-22_TODO-STRICT-ROW-SPECIFIC-SOURCE-ENVELOPE-RECOVERY-2026-07-22.md
  - imports/2026-07-22_strict_row_specific_source_envelope_recovery.json
task: TODO-STRICT-ROW-SPECIFIC-SOURCE-ENVELOPE-RECOVERY-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: journal
status: complete
supersedes: []
superseded_by:
---

# Strict Row-Specific Source-Envelope Recovery

Task: `TODO-STRICT-ROW-SPECIFIC-SOURCE-ENVELOPE-RECOVERY-2026-07-22`

## Attempted

I attempted the first requested gate for the S13 exchange-cell plus MF12 source-memory temperature path by joining the existing source/property release matrices, candidate-lane consequences, MF12 formula gate, and targeted literature model-form inventory. I did not use validation, holdout, external-test, or newly fitted evidence.

## Observed

The four nominal train rows are label-complete, but none has strict row-specific source-envelope pass. Salt1 remains partial because branch-specific source-envelope evidence is missing. Salt2, Salt3, and Salt4 remain mixed/outside/unknown against their current source families. The S13 exchange-cell lane is additionally blocked by absent same-label medium/fine exact-label rows and absent same-mask energy residual. MF12 remains diagnostic-only and not ready for train-only smoke.

## Inferred

The right action is fail-closed recovery, not release. A train-only S13+MF12 smoke can become meaningful only after the repaired S13 sampler lands nonempty rows, same-label mesh/GCI passes or fails with explicit QOI-level labels, the same masks support an exchange control-volume energy residual, and the source-envelope/source-property gate is refreshed for the exact candidate.

## Caveats

This package does not verify primary-source constants or source pages beyond the existing repo evidence. It preserves the current no-release state rather than attempting to infer strict source-envelope overlap from incomplete labels.

## Next Useful Actions

1. Monitor repaired sampler job `3310996`.
2. If it writes nonempty medium/fine rows, run the same-label mesh/GCI disposition for all four S13 QOIs.
3. If mesh/GCI does not fail closed, compute the same-mask exchange CV energy residual.
4. Only then run a train-only S13 exchange-cell plus MF12 source-memory temperature smoke row.
