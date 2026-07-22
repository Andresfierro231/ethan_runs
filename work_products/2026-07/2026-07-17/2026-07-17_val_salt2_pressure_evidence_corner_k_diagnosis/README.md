---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_pressure_map.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_unlock_queue.csv
tags: [val-salt2, pressure-evidence, corner-k, admission, diagnostic]
related:
  - .agent/status/2026-07-17_AGENT-503.md
  - .agent/journal/2026-07-17/val-salt2-pressure-evidence-corner-k-diagnosis.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
task: AGENT-503
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Pressure Evidence and Corner-K Diagnosis

## Answer

Corner K has `0` fit-admitted entries because the current evidence does not pass
ordinary component-K fit gates. All `12` preserved corner
rows remain diagnostic, and `12` of
them produce negative local centerline K after adjacent straight-loss
subtraction. That is not a physical negative-K claim; it is evidence that the
current tap/straight-reference construction over-subtracts the preserved
feature pressure loss.

For `val_salt2`, the pressure map is still useful as external-test diagnostic
evidence, but all `6` branch pressure rows have
`0` ordinary `f_D`/`K` fit-admitted entries. The branch rows are recirculation
masked, coarse/no-GCI, and in two rows have pressure-basis conflict review flags.

## Files

- `val_salt2_pressure_evidence_status.csv`: branch-level pressure status and
  fit-use policy for `val_salt2`.
- `corner_k_failure_modes.csv`: row-level corner-K failure modes, including the
  straight-loss over-subtraction ratio.
- `corner_k_gate_matrix.csv`: explicit pass/fail gates for every current corner
  row.
- `pressure_evidence_use_policy.csv`: allowed and forbidden uses.
- `next_pressure_evidence_queue.csv`: minimum work before any ordinary corner-K
  fit.
- `decision.json` and `summary.json`: machine-readable answer and counts.

## Guardrails

- No native CFD output was modified.
- No registry/admission state was modified.
- No scheduler, OpenFOAM, Fluid, or duplicate pressure-ladder job was run.
- No `val_salt2` fitting, tuning, model selection, or corner-K admission change
  was made.
