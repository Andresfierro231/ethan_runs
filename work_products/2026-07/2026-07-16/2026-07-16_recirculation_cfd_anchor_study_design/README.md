---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/decision_note.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - .agent/status/2026-07-16_AGENT-471.md
  - .agent/status/2026-07-16_AGENT-475.md
tags: [recirculation, cfd-run-design, upcomer-onset, insulation, uncertainty]
related:
  - .agent/status/2026-07-16_AGENT-478.md
  - .agent/journal/2026-07-16/recirculation-cfd-anchor-study-design.md
task: AGENT-478
date: 2026-07-16
role: CFD-study-design/Writer/Implementer/Tester
type: work_product
status: complete
---
# Recirculation CFD Anchor Study Design

This package proposes the next CFD run matrix for upcomer recirculation/onset
anchors. It does not stage or submit jobs.

## Study Decision

Run no new duplicate high-Q nominal-insulation Salt4 cases until jobs `3299610`
and `3299620` report enough status. The next independent knob should be real
insulation mutation on a Salt3 Jin anchor:

- high-Re / high-insulation cell-off sentinel: `salt3_jin_q1500w_hiins_onset_anchor`
- low-Q / low-insulation cell-max sentinel: `salt3_jin_q0150w_loins_onset_anchor`
- small `Q x insulation` matrix: `3 x 3` rows at `250`, `500`, and `1000 W`
  crossed with `hiins`, `baseline`, and `loins`.

`hiins` means more insulation / lower passive external `h` (`0.5x`); `loins`
means less insulation / higher passive external `h` (`2.0x`). This must be
verified in both root `0/T` and the collated restart field read by `foamRun`.

## Outputs

- `proposed_cfd_run_matrix.csv`
- `small_q_insulation_matrix.csv`
- `required_output_contract.csv`
- `mesh_time_uncertainty_plan.csv`
- `active_high_heat_context.csv`
- `tomorrow_start_here.md`
- `summary.json`

## Counts

- Proposed rows: `11`.
- Sentinel rows: `2`.
- Matrix rows: `9`.

## Scientific Guardrail

These runs can produce onset anchors and recirculation classifier evidence.
They should not be used as ordinary upcomer `Nu`, `f_D`, or component `K` fits
unless reverse-flow and uncertainty gates pass.
