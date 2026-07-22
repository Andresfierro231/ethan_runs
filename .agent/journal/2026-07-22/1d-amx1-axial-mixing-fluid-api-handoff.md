---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_amx1_axial_mixing_fluid_api_handoff/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_axial_mixing_dry_contract/README.md
tags: [journal, amx1, axial-mixing, thermal-blocker, model-form]
related:
  - .agent/status/2026-07-22_TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22.md
  - imports/2026-07-22_1d_amx1_axial_mixing_fluid_api_handoff.json
task: TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Coordinator / Writer / Reviewer
type: journal
status: complete
---
# 1D AMX1 Axial-Mixing Fluid API Handoff

## Attempted

Claimed the open AMX1 Fluid API handoff row after completing the thermal
accounting packet. Read the AMX1 dry contract, current forward-predictive model
map, and completed AMX1 intake summaries for Salt1-Salt4 bounded comparison,
localized forms, lower multipliers, gradient clipping, and parent-cell physics
revision.

## Observed

The original dry contract said Fluid lacked AMX1 fields and ledgers. Later
external Fluid work already supplied enough API/root/ledger support to run
multiple AMX1 smoke families. Across five reviewed campaigns, the rows were
runtime-clean at the reported audit level: finite roots passed, enabled AMX1
ledgers were nonzero, and ledgers were conservative.

The scientific progression gate did not pass. The Salt1-Salt4 bounded
diagnostic comparison worsened all-probe, TP, TW, and TW-without-TW10 RMSE.
Salt2 localized and lower-multiplier forms did not produce a candidate ready
for broader comparison. Gradient clipping reduced the positive core-temperature
delta but still worsened all-probe and TP RMSE. The parent-cell physics
revision was a real form change, but it also worsened all-probe and TP RMSE and
performed worse than the clipped pairwise result.

## Inferred

AMX1 is no longer blocked by basic API plumbing. It is blocked by source
physics: the tested forms do not have enough evidence for where exchange should
act, what directionality or limiting law is physical, or how to bound strength
without using target residuals. Retrying scalar multipliers would be fitting by
another name and would not unlock the thesis blocker.

## Caveats

This package did not inspect or edit external Fluid code. It relies on the
completed intake summaries and forward-predictive map as read-only evidence.
The packet does not change admission status, release source/property labels, or
score validation/holdout/external rows.

## Next Useful Actions

1. Move primary thermal blocker work to setup-only wall/test-section/passive
   boundary candidates.
2. Continue S13 same-label medium/fine generation or harvest so exchange QOIs
   can receive same-label mesh/GCI disposition.
3. Reopen AMX1 only after a source-evidence packet identifies signed local
   exchange direction, wall/core stratification shape near TW5/TW6, or a
   source-bounded exchange envelope.
