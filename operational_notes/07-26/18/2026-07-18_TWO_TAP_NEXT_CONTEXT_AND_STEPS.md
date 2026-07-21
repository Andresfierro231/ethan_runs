---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/final_gate_review.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/nonrecirculating_anchor_request.csv
tags: [handoff, hydraulics, pressure-ledger, two-tap, component-k]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/status/2026-07-18_TODO-TWO-TAP-NEXT-CONTEXT-HANDOFF.md
  - .agent/journal/2026-07-18/two-tap-next-context-handoff.md
  - imports/2026-07-18_two_tap_next_context_handoff.json
  - .agent/blockers.yml
task: TODO-TWO-TAP-NEXT-CONTEXT-HANDOFF
date: 2026-07-18
role: Hydraulics/Writer
type: operational_note
status: complete
---
# Two-Tap Next Context And Steps

This note is the start-here handoff for the `corner_lower_right` two-tap thread
after the July 18 raw endpoint sampler, pressure/basis recirculation audit, and
remaining-gates review. It exists so the next agent can continue without chat
logs and without accidentally turning diagnostic rows into F6 or component-K
training evidence.

## Open First

1. `.agent/BOARD.md`
2. `.agent/blockers.yml`
3. `operational_notes/maps/pressure-and-momentum-budget.md`
4. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/README.md`
5. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/README.md`
6. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/README.md`
7. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/README.md`
8. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/README.md`
9. `work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/README.md`

## Current State

The raw endpoint surface blocker is resolved only for the current staged
`corner_lower_right` endpoint samples. Six raw endpoint rows were harvested for
Salt2/Salt3/Salt4 at `lower_leg__s04` and `right_leg__s00`.

The pressure/velocity basis blocker is also resolved for these rows: static
pressure, `p_rgh`, hydrostatic, kinetic, density, velocity, and local dynamic
pressure terms are finite for all three pairs.

The rows are not ordinary component-K or F6 evidence. Every pair fails material
reverse-flow gates, with aggregate RAF about `0.763` and aggregate RMF about
`0.500`, far above the `<0.01` ordinary threshold. Component isolation routes
all rows to `apparent_cluster_only`, and same-QOI UQ is
`missing_no_GCI_diagnostic_only`.

Final July 18 admission state:

- `ordinary_component_k_candidates = 0`
- `component_k_admitted = false`
- `f6_fit_performed = false`
- decision:
  `diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ`

## Trusted Packages

- Raw endpoint sampler:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/`
- Pressure/basis recirculation audit:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/`
- Component isolation decision:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/`
- Same-QOI UQ status:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/`
- Separated admission review:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/`
- Non-recirculating-anchor request:
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/`
- F6 separation context:
  `work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/`

## Unresolved Blockers

Use `.agent/blockers.yml` as authoritative. The current open blockers for this
thread are:

- `two-tap-corner-lower-right-material-reverse-flow`
- `two-tap-corner-lower-right-component-isolation-fails`
- `two-tap-corner-lower-right-same-qoi-uq-missing`

How to address them:

- Material reverse flow: find or create a non-recirculating anchor, or claim a
  separate explicitly recirculation-modeled diagnostic path. Do not use the
  current rows as ordinary K/F6 rows.
- Component isolation: require a same-basis straight reference that does not
  make K negative and does not mix proxy/static/`p_rgh` bases. Otherwise keep
  the feature as apparent/cluster only.
- Same-QOI UQ: build a same-label, same-formula, same-sign mesh/time family for
  the same pressure-loss/K QOI. Do not borrow unrelated GCI.

## Active Board Awareness

Before any next action, check `.agent/BOARD.md`. On July 18, active
collision-sensitive rows included broader Monday dispatch work, Fluid/API work,
and scheduler monitor rows. Do not edit generated index files, Fluid source
files, registry/admission state, or active task-owned packages unless a new row
claims them explicitly.

## Next Task Sequence

### 1. Non-Recirculating Anchor Planning Row

Claim a new row before editing. Recommended task name:
`TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN`.

Purpose: choose whether `NR-CLR-01` or `NR-ALT-01` from
`nonrecirculating_anchor_request.csv` is feasible from existing or launchable
cases.

Outputs should include:

- `candidate_anchor_inventory.csv`
- `source_case_selection.csv`
- `staging_contract.csv`
- `endpoint_sampling_contract.csv`
- `same_qoi_uq_family_plan.csv`
- `launch_or_no_launch_decision.json`
- `README.md`
- `summary.json`

Acceptance: no scheduler launch yet unless this same row explicitly includes
launch scope and resource/monitor rules.

### 2. Staged-Copy Sampler Row

If an anchor is selected, claim a separate cfd-pp row for staged-copy sampling.
Use the existing two-tap staged sampler pattern, but emit a new dated package.

Required endpoint fields:

- `p`
- `p_rgh`
- `U`
- `rho`
- `T`
- face area
- face normal
- same-window RAF/RMF/SVF

For same-topology `corner_lower_right`, keep endpoint labels
`lower_leg__s04` and `right_leg__s00`. For an alternate feature, declare exact
mesh-station labels before launch.

Acceptance: raw rows are finite, source paths are recorded, direct native
solver outputs are not mutated, and aggregate RAF/RMF are computed from the
same window.

### 3. Gate Review Row

After raw anchor harvest, run a new gate package. It must evaluate, in order:

1. raw endpoint availability
2. pressure/velocity basis
3. recirculation thresholds
4. same-basis straight reference
5. component isolation
6. same-QOI UQ
7. separated admission decision

Acceptance for ordinary component K requires all gates to pass. If any gate
fails, emit diagnostic-only status and a blocker delta, not a fitted value.

### 4. F6 Work Stays Separate

F6 remains a separate legwise pressure-anchor lane. A future two-tap component
anchor must not be blended into F6 unless a separately claimed F6 review row
proves ordinary anchor eligibility against the `F3_shah_apparent` baseline and
keeps source/property labels intact.

## Output Contract For Future Rows

Every future two-tap package should preserve:

- exact source case paths
- staged-copy paths
- endpoint labels and geometric basis
- pressure basis and sign convention
- velocity/dynamic-pressure basis
- density/temperature basis
- recirculation metrics with thresholds
- straight-reference method and basis
- same-QOI UQ status
- admission decision separated from diagnostics
- explicit flags for native-output, registry, scheduler, Fluid, F6, and
  component-K mutation/admission state

## Assumptions To Preserve

- Existing July 18 raw endpoint values are authoritative for the current
  `corner_lower_right` diagnostic rows.
- Negative `K_local` after straight subtraction is a failed-basis/isolation
  signal, not a value to clip.
- Material reverse flow blocks ordinary component-K and ordinary F6 use unless
  a later task writes a new, explicit recirculation-modeled diagnostic contract.
- Same-QOI uncertainty must match labels, formula, and sign convention.
- A request package is not permission to launch scheduler work.

## Do Not Do

- Do not fit F6 from the current two-tap rows.
- Do not admit component K from the current two-tap rows.
- Do not clip negative K.
- Do not introduce a hidden global multiplier.
- Do not invent endpoint pressure, uncertainty, or recirculation metrics.
- Do not mutate native OpenFOAM outputs.
- Do not edit registry/admission state.
- Do not launch solver/postprocessing work without a new board row that grants
  scheduler scope and staged-output paths.
