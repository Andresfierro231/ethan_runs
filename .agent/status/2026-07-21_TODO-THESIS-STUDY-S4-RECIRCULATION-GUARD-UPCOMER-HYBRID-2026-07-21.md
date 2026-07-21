---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/summary.json
tags: [thesis-study, recirculation, upcomer, source-gate, status]
related:
  - .agent/journal/2026-07-21/thesis-study-s4-recirculation-guard-upcomer-hybrid.md
  - imports/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid.json
task: TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21

## Objective

Consolidate recirculation/upcomer evidence into a thesis-ready guard study
that disables ordinary single-stream closure labels where current gates fail.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/`.

Key results:

- ordinary single-stream candidates reviewed: `90`;
- ordinary closure disable rows: `4`;
- reverse-flow/exchange diagnostic rows: `45`;
- exchange variables reviewed: `14`;
- scoreable/admitted rows: `0`;
- ordinary upcomer `Nu/f_D/K` rows admitted: `0`;
- exchange-cell coefficient rows admitted: `0`.

The result is positive as a guard and negative as an admission: current
recirculation evidence supports excluding ordinary one-stream labels, but not
fitting or scoring an exchange cell.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21.md`
- `.agent/journal/2026-07-21/thesis-study-s4-recirculation-guard-upcomer-hybrid.md`
- `imports/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid.json`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/**`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/build_s4_recirculation_guard.py`: passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/build_s4_recirculation_guard.py work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/check_s4_recirculation_guard.py`: passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/check_s4_recirculation_guard.py`: passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid`: passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid --strict`: passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid`: passed.

## Unresolved Blockers

- `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window pressure/energy
  residuals, and same-QOI uncertainty remain missing for exchange-cell scoring.
- Ordinary closure rows remain blocked by recirculation, source-envelope,
  sign/heat-balance, and same-QOI gates.

## Guardrails

- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched.
- Fluid/external repos: not edited.
- Fitting/tuning/model selection: not performed.
- Ordinary upcomer `Nu/f_D/K`, F6, component `K`, and exchange coefficients:
  not admitted.
- Blocker register and generated docs index: not edited.
