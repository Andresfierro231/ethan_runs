---
provenance:
  - tools/analyze/build_heatloss_upcomer_exchange_evidence_extraction.py
  - tools/analyze/test_heatloss_upcomer_exchange_evidence_extraction.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/summary.json
tags: [thermal-modeling, heat-loss, upcomer, recirculation, status]
related:
  - .agent/journal/2026-07-21/heatloss-upcomer-exchange-evidence-extraction.md
  - imports/2026-07-21_heatloss_upcomer_exchange_evidence_extraction.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff/README.md
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION

## Objective

Build the Phase 2 follow-on upcomer exchange evidence-extraction contract and
preflight: map missing `V_recirc`, `mdot_exchange`, `tau_recirc`, wall-core
Delta T, pressure residual, energy residual, and same-QOI UQ fields to sampler
requirements and case/time windows, without launching extraction or admitting
exchange/internal-Nu fits.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/`.

- Contract rows: `21` (`3` mainline cases by `7` required field groups).
- Required field groups: `local_reverse_flow`, `recirculation_volume`,
  `exchange_rate`, `thermal_state`, `pressure_basis`, `wall_source_terms`,
  `same_qoi_uq`.
- Case/time queue rows: `3` for salt 2 (`7915` s), salt 3 (`7618` s), and
  salt 4 (`10000` s).
- Exchange fit allowed now: `false`.
- Scorecard use allowed now: `false`.
- Residual absorbed into internal Nu: `false`.

The package keeps current RAF/RMF/SVF and energy-residual evidence in a
diagnostic lane. It makes the next sampler requirements explicit and preserves
the rule that heat residual cannot be hidden in internal Nu.

## Changes Made

- `tools/analyze/build_heatloss_upcomer_exchange_evidence_extraction.py`
- `tools/analyze/test_heatloss_upcomer_exchange_evidence_extraction.py`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/upcomer_exchange_extraction_contract.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/sampler_field_map.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/case_time_window_queue.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/no_admission_guardrail.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/next_agent_handoff.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/summary.json`
- `.agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION.md`
- `.agent/journal/2026-07-21/heatloss-upcomer-exchange-evidence-extraction.md`
- `imports/2026-07-21_heatloss_upcomer_exchange_evidence_extraction.json`
- `.agent/BOARD.md` own row update

## Validation

- `python3.11 -m py_compile tools/analyze/build_heatloss_upcomer_exchange_evidence_extraction.py tools/analyze/test_heatloss_upcomer_exchange_evidence_extraction.py`:
  passed.
- `python3.11 tools/analyze/build_heatloss_upcomer_exchange_evidence_extraction.py`:
  passed; generated `21` contract rows, `7` field-map rows, and `3` case/time
  queue rows.
- `python3.11 -m unittest tools.analyze.test_heatloss_upcomer_exchange_evidence_extraction`:
  passed, `7` tests.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION`:
  passed; found status, journal, and import artifacts.

## Unresolved Blockers

- `tools/extract/sample_upcomer_convection_cell.py` only has partial support
  for local reverse-flow metrics; it does not emit `V_recirc`,
  `mdot_exchange`, `tau_recirc`, paired main/cell thermal states, pressure
  residual, or same-QOI UQ.
- A new board row is needed before sampler design or compute-node execution.
- Same-QOI mesh/time uncertainty must be paired to the exact exchange-state
  QOIs before any Phase 4B rescore or final scorecard use.

## Guardrails

- Native solver outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched.
- Solver/postprocessing/sampler: not launched.
- Fluid source and external repositories: not edited.
- Fitting/tuning/model selection: not performed.
- Closure admission and scorecard trigger: not changed.
- Blocker register and generated docs index: not edited.
- Heat residual: kept separate from internal Nu.
