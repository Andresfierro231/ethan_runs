---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/component_isolation_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/same_qoi_uncertainty_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/final_gate_review.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/nonrecirculating_anchor_request.csv
tags: [pressure-ledger, two-tap, gates, component-k]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-REMAINING-GATES-AND-ANCHOR-REQUEST.md
  - imports/2026-07-18_two_tap_remaining_gates_and_anchor_request.json
  - .agent/blockers.yml
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-REMAINING-GATES-AND-ANCHOR-REQUEST
date: 2026-07-18
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Remaining Gates And Anchor Request

## Attempted

Converted the remaining `corner_lower_right` two-tap repair work into four
staged evidence packages from existing files only:

- component-isolation/apparent-cluster decision
- same-QOI uncertainty status
- separated diagnostic-versus-admission review
- non-recirculating-anchor request

The work intentionally stayed outside F6 and component-K admission. It did not
launch solver/postprocessing jobs, alter native OpenFOAM outputs, edit registry
state, or refresh generated documentation indexes.

## Observed

The component-isolation package finds no admissible ordinary straight-reference
path for the three Salt2/Salt3/Salt4 `corner_lower_right` rows. The prior
centerline option is already negative on the old proxy basis, the static raw
endpoint option is mixed-basis and recirculation-contaminated, and the `p_rgh`
minus prior straight option remains negative and recirculation-contaminated.
Each row therefore routes to `apparent_cluster_only`.

The same-QOI UQ package finds no exact same-label, same-formula, same-sign
mesh/time family for these rows. Each row is marked
`missing_no_GCI_diagnostic_only`; no borrowed uncertainty was attached.

The separated admission package keeps all three rows diagnostic-only. Raw
surface sampling and pressure-basis checks are complete, but recirculation,
component isolation, and same-QOI UQ gates fail.

The anchor request package emits two request rows: a preferred same-topology
non-recirculating `corner_lower_right` anchor and an alternate comparable
two-tap component candidate. Both are requests only; no run was launched.

## Inferred

The current harvested two-tap rows can support a documented apparent/cluster
diagnostic, but they cannot support ordinary component-K closure or F6 evidence.
The next productive route is to obtain a non-recirculating same-topology anchor
with the same endpoint fields and recirculation metrics, then repeat the raw
endpoint and gate sequence on staged copies.

## Assumptions

- Existing raw endpoint rows are the authoritative harvested values for this
  task.
- Existing pressure-basis/recirculation metrics are the authoritative material
  reverse-flow gate for this task.
- A valid ordinary component-K row requires a nonnegative same-basis pressure
  drop, non-recirculating endpoint material flow, and same-QOI uncertainty.
- Missing same-QOI UQ cannot be replaced by unrelated or opposite-sign
  families without a separate documented admission rule.
- A non-recirculating anchor request is a future evidence contract, not
  permission to launch solver work or admit current rows.

## Caveats

The packages do not evaluate whether an explicit recirculation-modeled loss law
could be useful. They only decide whether the current two-tap endpoint evidence
can become ordinary component-K or F6 evidence under the existing gate contract.

The alternate anchor request is intentionally broad. It must be narrowed by a
later owned task before any scheduler or Fluid/source-tree action.

## Next Useful Actions

Claim a separate launch/planning row for a non-recirculating anchor if the team
wants new evidence. That row should identify source cases, staging paths,
resource limits, acceptance gates, and monitor handoff rules before scheduler
submission.

Keep the current `corner_lower_right` rows out of component-K and F6 training
sets unless a later documented rule supersedes the recirculation, isolation,
and same-QOI UQ blockers.
