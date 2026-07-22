---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/split_legal_case_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/pm10_split_use_decision.csv
  - work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard/runtime_input_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate/runtime_input_audit.csv
tags: [thesis, cfd, legal-use, runtime-contract, no-score]
related:
  - .agent/status/2026-07-22_TODO-THESIS-EVIDENCE-PACKET-CFD-LEGAL-USE-MATRIX-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-evidence-packet-cfd-legal-use-matrix.md
  - imports/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix.json
task: TODO-THESIS-EVIDENCE-PACKET-CFD-LEGAL-USE-MATRIX-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: work_product
status: complete
---
# CFD Legal-Use Matrix

Decision: `cfd_evidence_legal_use_matrix_ready_no_scoring_no_runtime_leakage`.

This packet gives the external thesis writer and later model-admission agents a
single table set for legal CFD evidence use. It separates thesis evidence from
runtime prediction inputs and preserves the train/support/holdout/external-test
split.

Key outcomes:

- evidence classes: `8`
- case split rows: `16`
- explicitly forbidden runtime input rows: `6`
- PM10 terminal evidence rows admitted for future planning: `4`
- current protected score allowed: `False`

Outputs:

- `cfd_legal_use_matrix.csv`
- `case_split_legal_use_table.csv`
- `runtime_forbidden_input_bans.csv`
- `writer_claim_boundary.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

Only the files listed above are canonical regenerated outputs for this packet.
Additional CSV/Markdown files in this directory came from a near-simultaneous
draft packet pass and are retained as supplemental, noncanonical material until
a later cleanup task explicitly reviews or removes them.

Guardrails: no native CFD/OpenFOAM output, registry/admission state, scheduler
state, Fluid source, external repository, validation/holdout/external-test
score, final score, source/property release, candidate freeze, or runtime input
contract was changed.
