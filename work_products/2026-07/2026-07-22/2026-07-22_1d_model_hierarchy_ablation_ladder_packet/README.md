# 1D Model Hierarchy And Ablation Ladder Packet

Decision: `hierarchy_ablation_ladder_ready_no_freeze_no_score`.

This package assembles the current 1D thesis evidence into a staged hierarchy.
It reports no final predictive score values and freezes no candidate.

## Main Result

The defensible model-development path is still:

`train-only full solve -> attribution -> freeze -> validation -> holdout -> external-test`.

Current evidence is strong enough for thesis structure: setup-only runtime
legality, pressure-basis negative evidence, S12 thermal residual ownership,
recirculation/onset diagnostic evidence, TP/TW projection mapping, AMX1 handoff
boundaries, and PM10 future-holdout status. It is not strong enough to release
a source/property correction, ordinary upcomer closure, exchange-cell
coefficient, or final predictive score.

## Outputs

- `model_hierarchy_ladder.csv`
- `ablation_evidence_matrix.csv`
- `freeze_prerequisite_gate_table.csv`
- `final_score_guardrail_table.csv`
- `figure_caption_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
