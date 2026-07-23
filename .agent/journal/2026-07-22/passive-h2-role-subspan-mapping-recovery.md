---
task: TODO-PASSIVE-H2-ROLE-SUBSPAN-MAPPING-RECOVERY-2026-07-22
provenance:
  generated_by: tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py
  task_id: TODO-PASSIVE-H2-ROLE-SUBSPAN-MAPPING-RECOVERY-2026-07-22
tags: [journal, PASSIVE-H2, patch-subspan, setup-UQ]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/salt34_runtime_smoke_eligibility.csv
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/same_qoi_setup_only_uq_results.csv
---
# PASSIVE-H2 Role/Subspan Mapping Recovery

## Attempted

Read the thermal boundary patch-role table, PASSIVE-H2 runtime-smoke package,
source-backed setup-basis package, split-disposition packet, nominal
source/property preflight, candidate gate, and runtime-operator setup-UQ
sensitivity rows.

## Observed

All five H2 source families have finite setup patch/subspan coverage in Salt2,
Salt3, and Salt4. The recovered roles include ambient, cooler, heater,
junction, and test-section patch groups. The existing setup-UQ table contains
finite train-context deltas for heat-ledger, mass-flow, projected temperature,
and passive-operator QOI labels.

## Inferred

The prior subspan blocker can be relaxed for setup/runtime-smoke support: the
patch-role table is sufficient to run Salt3/Salt4 diagnostic smoke in a later
owned compute row. The blocker is not removed for admission. Exact
source/property release, split legality for scoring, candidate freeze, and
final scoring remain closed.

## Next Useful Actions

Claim the Salt3/Salt4 diagnostic runtime-smoke row, then generate exact
target-minus/target/target-plus runtime summaries for the same QOI labels.
After those land, rerun the candidate-specific source/property gate.
