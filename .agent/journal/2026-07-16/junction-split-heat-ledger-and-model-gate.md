---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_patch_contract.csv
  - work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling/patch_wall_shell_temperatures.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/cfd_heat_audit_by_run.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/case_pressure_ladder_admission_summary.csv
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/model_update_gate.csv
tags: [junction-heat-loss, heat-audit, one-d-model, pressure-admission]
related:
  - .agent/status/2026-07-16_AGENT-473.md
  - imports/2026-07-16_junction_split_heat_ledger_and_model_gate.json
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger_and_model_gate.md
task: AGENT-473
date: 2026-07-16
role: Writer/Tester
type: journal
status: complete
supersedes: []
superseded_by:
---

# Junction Split Heat Ledger And Model Gate

Implemented the evidence-first plan from the pressure/heat audit follow-up. The reusable builder consumes only existing postprocessed evidence and writes a package under `work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/`.

The key source was `external_bc_patch_contract.csv`, which carries per-patch realized junction heat and setup boundary metadata for Salt2/Salt3/Salt4 mainline. Joining to `patch_wall_shell_temperatures.csv` adds wall-shell temperature proxies for setup-only future parameterization.

The split closes exactly against AGENT-462 aggregate junction/stub losses:
- Salt2: 39.128350 W.
- Salt3: 43.234691 W.
- Salt4: 48.485216 W.

Dominant pattern: upper-right is the largest physical bucket in all three mainline cases, about 36% of aggregate junction/stub loss. The lower-left and lower-right buckets are each about 19-20%, and upper-left is about 24-25%. This supports a localized junction/stub model form, but the evidence is still mainline-only.

The model update gate failed intentionally. It should not proceed to Fluid edits yet because val_salt2 lacks patch-split junction heat, Salt2/Salt4 perturbations lack comparable split ledgers, and the pressure-corner K lane remains diagnostic with zero admitted fit rows. Realized `wallHeatFlux` remains target evidence only, never a runtime input.

Recommended next implementation task: harvest or promote patch-split junction heat ledgers for val_salt2 and the perturbation cases, then rerun this gate. If the user wants a narrower Salt2-4-only candidate model experiment, that should be claimed as a separate explicitly diagnostic Fluid task.

Validation completed:
- `python3.11 -m unittest tools.analyze.test_junction_split_heat_ledger_and_model_gate`
- `python3.11 tools/analyze/build_junction_split_heat_ledger_and_model_gate.py`

## Start Here Tomorrow

Open these first:
- `work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger_and_model_gate.md`
- `work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/model_update_gate.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/case_heat_ledger_admission.csv`
- `tools/analyze/build_junction_split_heat_ledger_and_model_gate.py`

Current trusted facts:
- Salt2/Salt3/Salt4 mainline have patch-split junction heat ledgers and close to AGENT-462 aggregate heat loss.
- Upper-right is consistently the largest physical junction/stub bucket.
- val_salt2 has only aggregate section heat, not patch-split junction heat.
- Salt2/Salt4 perturbation cases have pressure maps but no comparable split heat ledgers.
- Pressure corner K remains diagnostic: zero admitted pressure fit rows and zero low-recirculation branch rows in the cited admission table.

Next task sequence:
1. Claim a new task before editing.
2. Harvest or promote patch-split junction heat ledgers for missing validation/perturbation cases, starting with val_salt2 because it is the external validation case.
3. Preserve the same output contract: patch ledger, physical-bucket ledger, case admission table, model gate, manifest, status, and journal.
4. Rerun the AGENT-473 builder or a successor builder and require the model gate to pass before any Fluid model edit.

Do not do:
- Do not submit duplicate pressure ladder jobs.
- Do not use realized CFD `wallHeatFlux` as a runtime Fluid model input.
- Do not fit corner K values from the current pressure evidence.
- Do not edit external Fluid files without a separate non-overlapping board claim in `../cfd-modeling-tools`.
