---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/s11_s15_unblock_queue.csv
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/salt1_source_envelope_gate_matrix.csv
tags: [salt1, predictive-1d, source-envelope, start-here]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/status/2026-07-22_TODO-SALT1-BRANCH-SOURCE-ENVELOPE-RECOVERY-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/README.md
task: TODO-SALT1-BRANCH-SOURCE-ENVELOPE-RECOVERY-2026-07-22
date: 2026-07-22
role: Forward-pred / Writer
type: operational_note
status: complete
---
# Salt1 Branch Source-Envelope Recovery Start-Here

## Why This Exists

Salt1 is part of the final Salt1-4 nominal training envelope, but the final
predictive model cannot freeze until Salt1 has row-specific runtime-legal
source-envelope evidence. The completed Salt1 runtime smoke proved execution is
possible diagnostically; this note records why that is still not enough for
source/property release.

## Files To Open First

- `work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/salt1_branch_source_evidence_matrix.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/salt1_source_envelope_gate_matrix.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/s11_s15_unblock_queue.csv`

## Trusted Packages

- `work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate/`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict/`
- `work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/`
- `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/`

## Current Decision

`salt1_branch_source_envelope_recovery_fail_closed_diagnostic_only`.

Four Salt1 families are recovered for diagnostic runtime use, but zero rows are
strict release-ready. The missing family is `junction`. The recovered
non-junction rows still carry wallHeatFlux/postProcessing provenance traces.

## Next Task Sequence

1. Recover Salt1 `junction` from setup-only mesh/geometry/boundary evidence.
2. Repair non-junction Salt1 area/coverage provenance so it no longer depends
   on realized wallHeatFlux or postProcessing-derived values.
3. Rerun candidate-specific S11/S15 source/property gates.
4. Freeze one Salt1-4 train-only candidate only if the gates pass.
5. Evaluate Salt2 +/-5Q and `val_salt2` without coefficient changes.

## Output Contract

Any follow-up recovery package should emit:

- row-level source family evidence;
- runtime-leakage audit;
- split-use audit;
- release gate matrix;
- exact source paths;
- no-release/no-score guardrails unless a separate candidate-specific release
  row explicitly admits the evidence.

## Do Not Do

- Do not copy Salt2/Salt3/Salt4 junction values into Salt1 as a shortcut.
- Do not use Salt1 wallHeatFlux, CFD mdot, realized cooler duty, validation
  temperatures, or residual fills as runtime inputs.
- Do not fit, tune, score, freeze, or release source/property state from a
  recovery row.
