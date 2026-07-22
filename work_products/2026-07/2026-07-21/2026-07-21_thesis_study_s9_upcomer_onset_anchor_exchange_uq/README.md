---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/upcomer_exchange_cell_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight/exchange_variable_availability.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_terminal_source_readiness/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix/summary.json
tags: [thesis-dossier, s9, upcomer, recirculation, exchange-qoi, uncertainty, negative-result]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md
task: TODO-THESIS-STUDY-S9-UPCOMER-ONSET-ANCHOR-EXCHANGE-UQ-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis S9 Upcomer Onset/Exchange UQ

## Decision

S9 closes as `negative_result_s11_still_blocked`.

The study enriches the recirculation-validity evidence but does not unblock
S11. It finds `14` grouped onset/exchange evidence
rows, `6` exchange-QOI contract rows, and
`0` S11-ready upcomer candidates.

## What S9 Establishes

- Existing upcomer evidence supports a recirculating/exchange-cell interpretation.
- Ordinary single-stream upcomer `Nu`, `f_D`, and K remain disabled.
- `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window pressure residuals, and
  same-QOI uncertainty remain the gating evidence for any future exchange-cell
  candidate.
- No S11 source/property refresh may start from S9 until exactly one candidate
  passes the S9 release gate.

## Files

| File | Use |
| --- | --- |
| `onset_anchor_ledger.csv` | Case-family recirculation/onset summary. |
| `near_onset_gap_table.csv` | Terminal, QOI, and sampler-input blockers. |
| `exchange_qoi_contract.csv` | Required `V_recirc`/`mdot_exchange`/`tau_recirc` and supporting QOI contract. |
| `same_window_uq_requirements.csv` | Same-QOI/time/mesh UQ requirements. |
| `s9_admission_gate_matrix.csv` | S9 gates and S11 effects. |
| `s11_unblock_decision.csv` | Machine-readable S11 decision from S9. |
| `source_manifest.csv` | Exact source paths and mutation flags. |
| `summary.json` | Machine-readable summary. |

## Guardrails

No solver, sampler, harvest, scheduler action, Fluid edit, external edit,
fitting, model selection, closure admission, ordinary upcomer closure reopening,
generated-index refresh, or S11 trigger was performed.
