---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation/source_operator_rows_train_only.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/nominal_train_release_audit.csv
tags: [journal, passive-h2, source-mapping, split, uq, no-release]
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SOURCE-MAPPING-SPLIT-UQ-PREFLIGHT-2026-07-22.md
  - imports/2026-07-22_passive_h2_source_mapping_split_uq_preflight.json
task: TODO-PASSIVE-H2-SOURCE-MAPPING-SPLIT-UQ-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Source Mapping / Split / UQ Preflight

## Attempted

Claimed a narrow PASSIVE-H2 blocker row after the runtime smoke showed nonzero
train-only heat-ledger movement. Built a deterministic preflight package that
does not run solvers or samplers. The package asks whether existing evidence is
enough to move from runtime-smoke support into mapping, split, UQ, or release.

## Observed

Salt2 runtime operator rows contain five source families with Fluid parent
segments and mapped wall-state sensors:

- `cooling_branch -> cooled_incline_pre_hx`
- `downcomer -> right_vertical`
- `junction -> bottom_horizontal_inlet`
- `lower_leg -> heated_incline`
- `upcomer -> upper_horizontal`

All five rows have finite setup fields and source-basis readiness, so
parent-segment mapping passes as support evidence. None has release-grade
subspan coverage/provenance, so subspan mapping fails closed.

Salt3 and Salt4 have analytic/reference PASSIVE-H2 targets, but no runtime-smoke
rows in the available package. The nominal source/property audit still has
`0/4` release-ready rows, and same-QOI UQ has target rows only, with no
target-minus/target-plus neighbors.

## Inferred

PASSIVE-H2 remains the best near-term thermal candidate, but the next blocker is
not runtime implementation. The next blocker is evidence resolution:
parent-to-subspan provenance, Salt3/Salt4 split legality or exclusion, and
same-QOI setup-only UQ.

No predictive coefficient should be fit from the Salt2 smoke. It is support
evidence that the implementation moves the heat ledger, not an admissible
closure.

## Caveats

- Subspan failure may be an evidence/documentation gap rather than a physics
  failure.
- Salt3/Salt4 analytic/reference rows are useful for context but not runtime
  evidence.
- Same-QOI UQ is not complete until neighbor rows exist for the exact labels in
  `same_qoi_uq_prerequisite_matrix.csv`.

## Next Useful Actions

1. Claim a release-grade H2 role-subspan mapping recovery row.
2. Then decide whether Salt3/Salt4 can be rerun as split-legal runtime smoke or
   must be excluded from candidate admission.
3. Then generate same-QOI setup-only UQ neighbor rows for the six listed labels.
4. Rerun the candidate-specific source/property gate only after those pass.
