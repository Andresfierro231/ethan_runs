---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/recirculation_switch_lane_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/qoi_interface_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/evidence_availability_gate.csv
tags: [journal, recirculation, model-form, 1d-switch, upcomer]
related:
  - .agent/status/2026-07-22_TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22.md
  - imports/2026-07-22_1d_recirculation_switch_dry_contract.json
task: TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# 1D Recirculation Switch Dry Contract

## Attempted

Built a task-scoped dry switch contract from the current recirculation/onset
packet, MF09 recirculating upcomer gate, 1D regime map, hierarchy ladder,
source/property atlas, pressure low-recirculation anchor inventory, and the
active S13 sampler handoff.

## Observed

Salt2/Salt3/Salt4 all have active reverse-flow proxy evidence and blocked
closed-CV claims. The pressure anchor inventory reports `0` ordinary-flow pass
rows, so one-stream upcomer claims do not have the required low-recirculation
or nonrecirculating anchor basis. The same-QOI UQ status is current-coarse
diagnostic support only; the medium/fine exact-label rows are still pending
under the separate sampler task. Source/property release for the S13 exchange
cell remains false.

## Inferred

The evidence is strong enough to make a model-form gate decision: ordinary
one-stream upcomer `Nu/f_D/K/F6` claims must stay disabled for the current
recirculating upcomer evidence. It is not strong enough to admit an
exchange-cell coefficient or production exchange-cell state. The rigorous dry
switch therefore routes current Salt2/Salt3/Salt4 rows to a guarded
`signed_flow_junction_network` fallback, meaning mixed-sign/reverse-flow
topology is active but no signed-flow coefficient or net branch reversal claim
is admitted.

## Caveats

The signed-flow lane is a fail-closed dry routing state here, not a component
K/F6 or scalar junction resistance claim. The throughflow-plus-recirculation
lane is defined as architecture only until a defensible cell mask, interface
faces, wall/core faces, same-QOI UQ, source/property validity, and mesh/GCI
evidence are admitted under future rows.

## Next Useful Actions

1. Let the active S13 medium/fine exact-label sampler finish; do not rerun
   mesh/GCI before exact-label rows exist.
2. If the sampler succeeds, open a narrow post-sampler row to inspect
   `medium_fine_exact_label_qoi_rows.csv`, error logs, and mesh/GCI readiness.
3. Continue recirculation-cell segmentation from validated cell VTKs so the CV,
   exchange interface, and wall/core band come from one physical source.
4. Keep ordinary one-stream `Nu/f_D/K/F6` disabled until a separate
   low-recirculation/nonrecirculating anchor package admits the required basis.
