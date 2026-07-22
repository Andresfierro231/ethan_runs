---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_blocker_workthrough_progress/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/partition_stability_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract/required_input_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet/corrected_operator_family_ledger.csv
tags: [journal, predictive-1d, runtime-contract, passive-h2, open-cv]
related:
  - .agent/status/2026-07-22_TODO-PREDICTIVE-1D-STRONGEST-DIRECTION-RUNTIME-CONTRACT-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_strongest_direction_runtime_contract/README.md
  - imports/2026-07-22_predictive_1d_strongest_direction_runtime_contract.json
task: TODO-PREDICTIVE-1D-STRONGEST-DIRECTION-RUNTIME-CONTRACT-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Predictive 1D Strongest Direction Runtime Contract

## Attempted

Converted the strongest current model direction into a local executable
contract. The work consumed the blocker workthrough, S13 bulk heat-partition,
S13 open-CV residual contract, PASSIVE-H2 corrected-operator handoff, and
source/property unblock summaries.

## Observed

The generated candidate is `P1D-BULK-CV-H2-CAND001`. It has a real local
reference kernel now: exterior convection, exterior radiation, passive total
loss, and open-CV residual accounting. The residual function deliberately
returns an incomplete state when throughflow, storage, or named-loss lanes are
missing.

The input schema distinguishes legal setup/state inputs from blocked residual
lanes. The train-context PASSIVE-H2 target table covers Salt2, Salt3, and Salt4
with five passive component families per case. Those rows are target/context
evidence only; they are not admitted runtime inputs or protected scores.

## Inferred

This is the closest current route to a predictive 1D model because it does not
try to repair the thermal residual by fitting. It gives the model an external
heat-path operator and an explicit residual ledger. The model cannot become a
candidate until the separate runtime implementation row shows heat-ledger
movement and until source/property and same-basis endpoint evidence are
available.

## Contradictions And Caveats

The bulk heat-partition evidence is stable enough to guide model form, but it is
still diagnostic. It must not be turned into a global fitted multiplier.

PASSIVE-H2 has train-context numeric targets, but the current runtime path has
not yet demonstrated the needed radiation-enabled ledger change.

The open-CV residual equation is defined, but same-basis residual values remain
uncomputable today.

## Next Useful Actions

1. Claim/continue `TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22`.
2. Claim a row-specific source/property release repair row.
3. Claim the S13 throughflow endpoint/cp harvest preflight.
4. Only after those pass, claim a one-candidate train-only smoke row for
   `P1D-BULK-CV-H2-CAND001`.
