---
task: TODO-PASSIVE-H2-SUBSPAN-MAPPING-RELEASE-RECOVERY-2026-07-22
provenance:
  generated_by: tools/analyze/build_passive_h2_subspan_mapping_release_recovery.py
tags: [journal, PASSIVE-H2, subspan, release-gate]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery/salt2_subspan_release_gate.csv
---
# PASSIVE-H2 Subspan Mapping Release Recovery

## Attempted

Consumed the completed role/subspan recovery packet and mapped Salt2 source
families to setup patch/subspan support, area support, and release-grade status.

## Observed

Salt2 has setup subspan support for five of five source families. Only two
families have area-match support, and no row is marked release-grade now.

## Inferred

The subspan blocker is improved for diagnostic setup work but not released for
source/property or final-form admission. Downstream rows may cite setup support,
not a released numeric passive heat-loss claim.

## Next Useful Actions

Run the Salt2 same-QOI setup-UQ gate, then rerun the candidate source/property
gate. Keep Salt3/Salt4 diagnostic work separate until its active runtime-smoke
row closes.
