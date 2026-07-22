---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
tags: [journal, thermal, passive-h2, source-basis, release-gate]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-SOURCE-BACKED-BASIS-TABLE-2026-07-22.md
  - imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json
task: TODO-THERMAL-PASSIVE-H2-SOURCE-BACKED-BASIS-TABLE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 source-backed basis table

## Attempted

Started from the `2026-07-22_thermal_passive_h2_source_basis_release_preflight`
missing-provenance table and rebuilt the release decision against the later
setup-dictionary evidence in the predictive external-boundary and patch-role
packets.

## Observed

The setup-dictionary path supplies nonzero source-backed rows for the five
passive families: cooling branch, downcomer, junction, lower leg, and upcomer.
Each row carries boundary dictionary trace, area/hA/h, Ta/Tsur, emissivity,
wall-layer metadata, radiation policy, and a q-loss operator contract that is
independent of Phase E diagnostic state.

## Inferred

The prior fail-closed source-basis preflight is superseded for this narrow
setup-dictionary basis, but not for numeric q-loss or fitted closure admission.
PASSIVE-H2 can now proceed to a separate one-train repair preflight, provided
the row is explicitly claimed and kept away from global multipliers, internal
Nu residual absorption, and validation/holdout scoring before freeze.

## Caveats

This is not a literature-fitted h-correlation release. The replacement for
wallHeatFlux-derived passive h provenance is the setup dictionary h/area/ambient
and layer basis, guarded by the heat-loss path contract and radiation guidance.

## Next Useful Actions

Claim a separate repair-preflight board row if continuing. Build only the dry
one-train input contract first; do not run a repair solve or freeze a candidate
inside this source-basis row.
