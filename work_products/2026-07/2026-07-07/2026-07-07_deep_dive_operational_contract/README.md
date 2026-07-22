# Deep Dive Operational Contract Handoff

Date: `2026-07-07`  
Task: `AGENT-188`  
Role: Coordinator / Writer

## Objective

Strengthen the CFD postprocessing / closure rigor deep dive so downstream
pressure-drop and F4 work cannot accidentally double-count buoyancy, fit the
wrong target, admit gated rows too early, or overclaim mdot predictivity while
the thermal driver remains mismatched.

## Outputs

- Updated:
  `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- Updated board TODOs:
  `TODO-PRESSURE-LEDGER-RIGOR`, `TODO-SALT1-STEADY-QUAL`,
  `TODO-RI-CORRECTED-F4`
- Status:
  `.agent/status/2026-07-07_AGENT-188.md`

## Key Contract Points

- `buoyancy_pressure()` remains the reversible driving-head term. F4/friction
  closures may only modify irreversible mechanical resistance or wall shear.
- Pressure-drop claims must come from a ledger that carries `p_rgh`, dynamic
  head, density-gradient buoyancy contribution, distributed mechanical loss,
  development/minor/residual terms, and admission flags.
- F4 targets must use de-buoyed `momentum_budget` quantities, not raw signed
  apparent-friction diagnostics.
- Corrected Salt Q rows require `operating_point_verdict=requalified`; rows with
  `needs_special_gate_scrutiny=True` require coordinator review even if another
  metric looks favorable.
- `F4_leg_class` exists but is not a Ri-corrected mixed-convection law.
- Salt 1 is provisional: stationary monitors, but short-window caveat, about
  `-2.08%` heat closure, missing Salt 1 nominal comparator confidence, and early
  ending of `salt1_jin_hi10q_corrected`.

## Exact Next Action

Implement `TODO-PRESSURE-LEDGER-RIGOR` as a separate task with a reproducible
CSV/JSON/README ledger and tests. The ledger must reproduce the July 1 Salt 2/3/4
de-buoyed momentum-budget rows before it is used to support any new F4 or
minor-loss claim.
