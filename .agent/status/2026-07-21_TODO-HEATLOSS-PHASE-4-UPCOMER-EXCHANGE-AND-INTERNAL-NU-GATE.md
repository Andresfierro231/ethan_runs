---
provenance:
  - tools/analyze/build_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py
  - tools/analyze/test_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/summary.json
tags: [thermal-modeling, heat-loss, upcomer, recirculation, internal-nu, status]
related:
  - .agent/journal/2026-07-21/heatloss-phase-4-upcomer-exchange-and-internal-nu-gate.md
  - imports/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/README.md
task: TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Forward-pred/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE

## Objective

Decide whether remaining upcomer/test-section thermal residuals can reopen
ordinary internal `Nu` or require throughflow-plus-recirculation/exchange-cell
handling before any later heat-loss scorecard claim.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/`
from existing Phase 2/3, LitRev, matched-plane, hybrid-upcomer, and onset-anchor
evidence. The result is a negative admission gate: current evidence supports
diagnostic exchange-cell/regime classification, but not exchange-cell
calibration and not ordinary internal-`Nu` reopening.

Key counts:

- exchange-readiness rows: `42`;
- ordinary single-stream reopening rows: `90`;
- aggregate mainline upcomer exchange rows: `3`;
- ordinary internal-`Nu` fit rows admitted: `0`;
- exchange-cell fit-ready rows: `0`;
- missing-evidence rows: `11`;
- Phase 5 trigger: `not_triggered`.

## Changes Made

- `tools/analyze/build_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py`
- `tools/analyze/test_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/upcomer_exchange_cell_readiness.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/ordinary_single_stream_nu_reopening_candidates.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/missing_exchange_nu_evidence_queue.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/phase4_decision_gate.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/runtime_internal_nu_audit.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/exchange_cell_readiness.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/ordinary_single_stream_nu_reopening_gate.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/heat_path_modeling_contract.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/phase4_release_gate.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/runtime_legality_audit.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/summary.json`
- `.agent/journal/2026-07-21/heatloss-phase-4-upcomer-exchange-and-internal-nu-gate.md`
- `imports/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate.json`
- `.agent/BOARD.md` own row update

## Validation

- `python3.11 tools/analyze/build_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py`:
  passed.
- `python3.11 -m py_compile tools/analyze/build_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py tools/analyze/test_heatloss_phase4_upcomer_exchange_and_internal_nu_gate.py`:
  passed.
- `python3.11 -m unittest tools.analyze.test_heatloss_phase4_upcomer_exchange_and_internal_nu_gate`:
  passed, `6` tests.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate`:
  passed.
- Structural CSV/JSON artifact check: passed, `11` CSV files plus
  `summary.json`.
- `python3 tools/docs/build_repo_index.py`: passed, refreshed generated docs
  index files `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`,
  and `.agent/catalog.csv`.
- `python3 tools/docs/build_repo_index.py --check`: passed, blocker register
  OK with `15` entries.
- `python3.11 tools/agent/finish_task.py --task-id TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE`:
  passed, found status, journal, and import artifacts; `finish_task: OK`.

## Unresolved Blockers

- `V_recirc`, `mdot_exchange`, `T_recirc`, and `tau_recirc` remain missing for
  calibration.
- Same-window pressure residual and exchange-cell energy closure are missing or
  partial.
- Same-QOI mesh/time uncertainty remains missing for recirculation metrics and
  residual targets.
- Current upcomer/test-section rows remain recirculating diagnostics, not
  ordinary single-stream `Nu`, `f_D`, `K`, or F6 evidence.
- Phase 5 remains trigger-gated because no runtime-legal heat-loss candidate or
  internal-`Nu` reopening candidate passed Phase 4.

## Guardrails

- Native solver outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched.
- Fluid/external repos: not edited.
- Solver/postprocessing/staged-copy launch: not performed.
- Fitting/tuning/model selection: not performed.
- Model scoring/admission: not performed.
- Blocker register: not edited.
