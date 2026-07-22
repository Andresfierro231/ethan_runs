---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/recirculation_onset_metric_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives/ordinary_upcomer_disable_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/closure_eligibility_decisions.csv
tags: [work-product, recirculation, model-form, 1d-switch, upcomer]
related:
  - .agent/status/2026-07-22_TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/1d-recirculation-switch-dry-contract.md
task: TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# 1D Recirculation Switch Dry Contract

This package converts the current recirculation evidence into a dry 1D
model-form switch. It does not fit coefficients, admit an exchange cell, rerun
mesh/GCI, release source/property rows, or mutate native CFD outputs.

Decision: `dry_recirculation_switch_contract_ready_no_coefficients_no_admission`.

## Contract

The switch has exactly three outputs:

- `one_stream`: allowed only when reverse-flow/recirculation evidence is
  inactive and low-recirculation or nonrecirculating anchors are admitted.
- `signed_flow_junction_network`: guarded dry fallback when topology indicates
  flow reversal or mixed signs but no closed exchange-cell volume/interface is
  admitted.
- `throughflow_plus_recirc_exchange_cell`: available only after a defensible
  recirculation CV, exchange interface, wall/core band, same-QOI UQ,
  source/property validity, and mesh/GCI evidence exist.

Current Salt2/Salt3/Salt4 rows select the guarded
`signed_flow_junction_network` lane because reverse-flow proxy evidence is
active while the exchange-cell admission gates remain blocked.

## Files

- `model_form_gate_update.csv`
- `recirculation_switch_lane_contract.csv`
- `dry_runtime_input_contract.csv`
- `qoi_interface_contract.csv`
- `current_case_switch_decisions.csv`
- `fail_closed_state_table.csv`
- `evidence_label_crosswalk.csv`
- `switch_pseudocode.md`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

Ordinary upcomer `Nu/f_D/K/F6` claims are disabled in recirculating upcomer
evidence. Exchange-cell coefficients remain disabled until a separate future
admission package has exact CV/interface/wall-core geometry, same-QOI UQ,
source/property validity, and mesh/GCI evidence.
