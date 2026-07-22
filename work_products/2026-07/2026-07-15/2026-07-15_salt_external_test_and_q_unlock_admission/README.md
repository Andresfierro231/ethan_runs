---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_expanded_case_set/case_summary.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh/README.md
tags: [salt-cfd, admission, external-test, perturbed-q, heat-loss-ledger]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-417
date: 2026-07-15
role: cfd-pp/Thermal-admission/Hydraulics/Writer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Salt External-Test And Perturbed-Q Unlock Admission

## Observed Facts

- Requested rows consolidated: `18`.
- Live selected +/-10Q rows remain blocked pending terminal harvest: `4`.
- `val_salt_test_2_coarse_mesh` has steady traces plus BC/material documentation, but no matching section heat-loss ledger in scoped evidence.
- Salt2/Salt4 +/-5Q PM5 rows now have wallHeatFlux and nondimensional fields, but F6/internal-Nu fit admission remains zero because recirculation/sign/admission gates fail.
- Salt3 nominal is steady and has Salt2-4 style BC/heat-loss diagnostic evidence; Salt3 corrected-Q high rows failed and low rows remain sensitivity/continuation candidates only.

## Inferred Interpretation

The best immediate thesis-safe use is thermal training/testing under explicit split policy. Closure-fit use is narrower: current PM5/F6/internal-Nu evidence is review-ready but not fit-admissible. `val_salt_test_2_coarse_mesh` is the right first external-test target, but it is blocked from thesis-strength external scoring until a matching heat-loss ledger and admission package exists.

## Usable Now

Use `split_admission_decisions.csv` as the authoritative table for this pass. In short:

- Salt1 nominal and Salt1 +/-10Q: user-policy thermal training candidates with Salt1 caveats; closure gates not admitted.
- Salt3 nominal: validation or user-training candidate only after the split policy is frozen.
- Salt2 +/-5Q: thermal holdout/testing candidates; not fit rows.
- Salt4 +/-5Q: user-policy thermal training candidates; not independent nominal baselines.

## Blocked Or Diagnostic

- `val_salt_test_2_coarse_mesh`: external-test candidate blocked by missing matching section heat-loss ledger.
- Salt3 low-Q corrected rows: sensitivity-only until continued or re-gated.
- Salt3 high-Q corrected rows: not admissible until failure cause is documented and a future rerun lands.
- Salt2/Salt4 +/-10Q: pending terminal harvest from live job `3293924` and dependent harvester `3295438`.
- F6/internal-Nu/upcomer closure rows: diagnostic/review-ready only; no fit-admissible rows in this pass.

## Files

- `salt_unlock_master_inventory.csv`
- `terminal_steady_state_evidence.csv`
- `bc_source_contracts.csv`
- `heat_loss_ledger_status.csv`
- `closure_gate_matrix.csv`
- `split_admission_decisions.csv`
- `pending_or_blocked_actions.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, scheduler state, registry/admission state, generated indexes, or external Fluid files were mutated. Realized CFD `wallHeatFlux` is treated as diagnostic target/output, not predictive runtime input.
