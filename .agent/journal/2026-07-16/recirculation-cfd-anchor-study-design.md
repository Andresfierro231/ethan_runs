---
provenance:
  - operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/decision_note.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - .agent/status/2026-07-16_AGENT-471.md
  - .agent/status/2026-07-16_AGENT-475.md
tags: [recirculation, cfd-run-design, upcomer-onset, insulation, uncertainty]
related:
  - .agent/status/2026-07-16_AGENT-478.md
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/README.md
task: AGENT-478
date: 2026-07-16
role: CFD-study-design/Writer/Implementer/Tester
type: journal
status: complete
---
# Recirculation CFD Anchor Study Design

User request: propose CFD runs to study:

- high-Re / high-insulation cell-off target,
- low-Q / low-insulation cell-max target,
- small `Q x insulation` matrix,
- with required outputs covering native fields, dimensionless numbers,
  recirculation metrics, steady-window status, and mesh/time uncertainty.

Decision: make a documented study only, not another submission. Live Salt4 jobs
`3299610` and `3299620` already cover high-Q nominal-insulation behavior. The
new independent study should use Salt3 Jin as the onset anchor and vary
insulation as a real passive-wall BC multiplier.

Key scientific choices:

- `hiins = more insulation = lower passive external h = 0.5x`.
- `loins = less insulation = higher passive external h = 2.0x`.
- Any future staged case must patch both root `0/T` and copied
  `processors64/<restart>/T`; old insulation labels are not trusted.
- Cooler fixed-Q sinks should be scaled from the parent heat ledger and then
  re-audited after insulation mutation, because passive ambient loss changes.
- Rows remain onset anchors, not ordinary upcomer `Nu`, `f_D`, or component `K`
  fits unless reverse-flow and uncertainty gates pass.

Outputs created:

- `proposed_cfd_run_matrix.csv`
- `small_q_insulation_matrix.csv`
- `required_output_contract.csv`
- `mesh_time_uncertainty_plan.csv`
- `active_high_heat_context.csv`
- `tomorrow_start_here.md`
- `summary.json`

Validation passed:

- `python3.11 -m py_compile tools/analyze/build_recirculation_cfd_anchor_study_design.py tools/analyze/test_recirculation_cfd_anchor_study_design.py`
- `python3.11 tools/analyze/build_recirculation_cfd_anchor_study_design.py`
- `python3.11 -m unittest tools.analyze.test_recirculation_cfd_anchor_study_design`

Guardrails: no native CFD outputs, registry/admission state, scheduler state,
case staging, or external Fluid files were mutated.
