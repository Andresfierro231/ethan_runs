---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/split_legal_case_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/pm10_split_use_decision.csv
  - work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard/runtime_input_audit.csv
tags: [thesis, cfd, legal-use, runtime-contract]
related:
  - .agent/status/2026-07-22_TODO-THESIS-EVIDENCE-PACKET-CFD-LEGAL-USE-MATRIX-2026-07-22.md
  - imports/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix/README.md
task: TODO-THESIS-EVIDENCE-PACKET-CFD-LEGAL-USE-MATRIX-2026-07-22
date: 2026-07-22
role: Writer / Reviewer / Tester
type: journal
status: complete
---
# CFD Legal-Use Matrix

## Attempted

Built a reproducible thesis evidence packet that converts split-policy,
runtime-audit, and PM10 terminal-admission context into a compact legal-use
matrix for CFD evidence.

## Observed

The split table still preserves four nominal final-training rows, four
training-support rows, two PM5 holdout rows, one external-test row, four PM10
future holdout rows, and one new-CFD future candidate row.

The PM10 terminal update admits terminal evidence for four Salt2/Salt4 +/-
10Q rows, but those rows still have `blind_score_allowed_now=no`,
`final_fit_allowed=no`, and `final_model_selection_allowed=no`.

The runtime audits explicitly forbid using CFD mdot, realized wall heat flux,
cooler duty, protected temperatures, protected residuals, and target-window
wall heat as runtime inputs.

## Inferred

The thesis can use CFD outputs as evidence for model-form limits, blocker
diagnosis, convergence context, and negative results. It cannot use realized
CFD outputs to repair a candidate at runtime or to score protected rows before
an independent freeze.

The useful thesis sentence is that CFD evidence is strong for explaining why
the predictive path is not yet admissible. It is not a final predictive score.

## Contradictions And Caveats

The canonical split permits nominal training in principle, but current
source/property release prevents fit/model-selection use now. This packet
therefore treats nominal train rows as legally separable from protected rows
while still blocked by the source/property gate.

## Next Useful Actions

1. Use `cfd_legal_use_matrix.csv` and `runtime_forbidden_input_bans.csv` when
   drafting Ch. 5-7 runtime-legality language.
2. Keep PM10 rows as future blind-holdout evidence until a candidate is frozen.
3. Do not score validation, holdout, or external-test rows from this packet.
4. Pair this packet with the source/property release atlas before reopening
   S11/S15 candidate-release work.
