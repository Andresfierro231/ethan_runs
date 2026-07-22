---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/final_window_admission_review.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/salt1_training_admission_package.csv
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/terminal_steady_state_evidence.csv
  - jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/**
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/**
tags: [salt1, admission, steady-state, closure-scorecard, board-cleanup]
related:
  - .agent/journal/2026-07-16/salt1-primary-evidence-admission-and-board-cleanup.md
task: AGENT-448
date: 2026-07-16
role: Coordinator/cfd-pp/Implementer/Tester/Writer/Cleaner
type: work_product
status: complete
---
# Salt1 Primary Evidence Admission And Scorecard

## Decision

Salt1 promotion to primary closure evidence: `yes`.

No compelling technical reason was found to keep Salt1 out of the primary evidence set. The terminal windows are stationary, the staged convergence monitor is diagnostic-only, and the cancellation provenance is operational rather than a solver failure. Use Salt1 as primary Salt1 closure/training evidence, while preserving the cancellation and perturbed-Q provenance in every downstream table.

## Salt1 Terminal Checks

| case | suspicious | total_Q drift W | max mdot rel drift | max TP drift K | max TW drift K | verdicts |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| salt1_nominal | no | 0 | 1.17115592878e-09 | 0 | 0 | steady |
| salt1_lo10q | no | 0 | 3.73805874001e-08 | 0 | 0 | steady |
| salt1_hi10q | no | 0 | 1.6316422713e-07 | 0 | 0 | steady |

## Admission-Status Scorecard

The final scorecard is intentionally organized by admission status, not by desired use. See `final_admission_status_scorecard.csv` for the machine-readable table with four allowed states: `admitted`, `validation-only`, `diagnostic-only`, and `blocked`.

## Files

- `salt1_terminal_monitor_metrics.csv`: per-monitor terminal-window drift and uncertainty.
- `salt1_convergence_audit.csv`: convergence-monitor and log-tail checks.
- `salt1_primary_evidence_decision.csv`: compact Salt1 promotion decision.
- `final_admission_status_scorecard.csv`: admission-status-first scorecard.
- `board_cleanup_summary.csv`: before/after board cleanup counts.
- `summary.json`: counts and acceptance flags.
