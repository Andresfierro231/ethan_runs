---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/current_case_switch_decisions.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/recirculation_onset_metric_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives/ordinary_upcomer_disable_gate.csv
tags: [status, recirculation, model-form, 1d-switch, upcomer]
related:
  - .agent/journal/2026-07-22/1d-recirculation-switch-dry-contract.md
  - imports/2026-07-22_1d_recirculation_switch_dry_contract.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/README.md
task: TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22

## Objective

Update the 1D model-form gate so current recirculation evidence disables
ordinary one-stream upcomer `Nu/f_D/K/F6` claims in the recirculating upcomer,
and publish a dry three-lane recirculation switch contract without fitting
exchange-cell coefficients.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/`.

Decision:
`dry_recirculation_switch_contract_ready_no_coefficients_no_admission`.

Key outcomes:

- switch outputs: `one_stream`, `signed_flow_junction_network`,
  `throughflow_plus_recirc_exchange_cell`
- current Salt2/Salt3/Salt4 selected lane:
  `signed_flow_junction_network` with
  `guarded_dry_fallback_not_net_branch_admission`
- current one-stream allowed cases: `0`
- current throughflow/exchange-cell allowed cases: `0`
- ordinary `Nu/f_D/K/F6` claim rows allowed: `0`
- exchange-cell coefficient fitting/admission: `false`

The contract is evidence-backed by current reverse-flow/recirculation evidence
but not coefficient-backed. It keeps the exchange-cell lane as architecture
only until defensible CV/interface/wall-core geometry, same-QOI UQ,
source/property validity, and mesh/GCI evidence exist.

## Changes Made

Added:

- `tools/analyze/build_1d_recirculation_switch_dry_contract.py`
- `tools/analyze/test_1d_recirculation_switch_dry_contract.py`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/`
- `imports/2026-07-22_1d_recirculation_switch_dry_contract.json`
- `.agent/journal/2026-07-22/1d-recirculation-switch-dry-contract.md`
- this status file

Updated:

- `.agent/BOARD.md` own row only

## Validation

- `python3.11 -m pytest tools/analyze/test_1d_recirculation_switch_dry_contract.py`:
  passed, `5` tests.
- `python3.11 -m py_compile tools/analyze/build_1d_recirculation_switch_dry_contract.py tools/analyze/test_1d_recirculation_switch_dry_contract.py`:
  passed.
- `python3.11 tools/analyze/build_1d_recirculation_switch_dry_contract.py`:
  passed and generated the package.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Scheduler action: `false`.
- Solver/postprocessing/sampler/harvest/UQ launched: `false`.
- Source/property or Qwall released: `false`.
- Mesh/GCI disposition rerun: `false`.
- Coefficient fitting/admission: `false`.
- S11/S12/S13/S15/S6 trigger: `false`.

## Unresolved Blockers

- The exchange-cell lane remains blocked because no closed recirculation CV,
  exchange interface, or wall/core band is admitted.
- Same-QOI UQ is currently coarse diagnostic support only; medium/fine
  exact-label rows are still pending the separate active sampler row.
- Source/property validity for the S13 exchange cell is not released.
- One-stream remains disabled for Salt2/Salt3/Salt4 because reverse-flow
  evidence is active and no admitted low-recirculation/nonrecirculating anchor
  exists.
