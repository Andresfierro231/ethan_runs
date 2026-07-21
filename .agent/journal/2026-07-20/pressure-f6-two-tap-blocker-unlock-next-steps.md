---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/paper_blocker_methods_note.md
tags: [journal, pressure-ledger, two-tap, f6, blocker-unlock]
related:
  - .agent/status/2026-07-20_TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS.md
  - imports/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps.json
task: TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# Pressure/F6/Two-Tap Blocker Unlock Next Steps

Task: `TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS`

## Work Completed

Built a blocker-unlock next-step package from the completed face-qref,
nonrecirculating staging, same-QOI launch, recirculating residual/model, high
heat monitor, and blocker-review artifacts. The package emits a blocker unlock
matrix, `CAND-001` terminal-readiness table, future sampler contract,
same-QOI UQ contract, recirculating apparent-K model contract, F6 gate sequence,
source manifest, summary, and paper methods note.

## Scientific Decision

No blocker is resolved yet. The current Salt2/Salt3/Salt4
`corner_lower_right` rows remain diagnostic because face-level reverse flow is
material, component isolation remains apparent/cluster-only, and same-QOI UQ is
missing. Ordinary component K can only be reviewed after a future low-reverse
same-topology sampler passes `RAF < 0.01` and `RMF < 0.01`, then component
isolation and same-QOI UQ. Recirculating rows stay in a named
section-effective pressure-residual lane.

## Next Evidence Needed

- terminal review of the `CAND-001` Salt4 high-heat/no-recirculation source
  cases;
- a separately claimed staged-copy endpoint sampler for `lower_leg__s04` to
  `right_leg__s00`;
- same-label/same-formula/same-sign mesh/time UQ for pressure residual and
  K-local formulas;
- later admission review only after all ordinary-flow and UQ gates pass.

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/build_pressure_f6_two_tap_blocker_unlock_next_steps.py`
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/test_pressure_f6_two_tap_blocker_unlock_next_steps.py`

Both passed before closeout.
