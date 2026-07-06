# Ethan Salt Analysis Checkpoint Suite

Generated: `2026-06-18`

This suite implements the Salt-first, closure-first roadmap as a sequence of
durable documented checkpoints built from the existing June 17 and June 18
Salt analysis artifacts. It does not reopen the shared June 15/17 extraction
path.

## Checkpoints

- `phase1_hydraulic_hardening/`
  Hydraulic fit gates, feature status, and buoyancy-aided section inventory.
- `phase2_heatloss_enthalpy_closure/`
  Heat-partition and enthalpy-closure checkpoint.
- `phase3_branch_trust_gate/`
  Thermal promotion gate for Salt branches and spans.
- `phase4_boundary_layer_context/`
  Boundary-layer and bulk-vs-centerline context package.
- `phase5_fit_ready_handoff/`
  Final fit-ready Salt subset and exclusion audit.

## High-level counts

- Phase 1 candidate hydraulic rows: `12`
- Phase 2 candidate enthalpy rows: `1`
- Phase 3 candidate branch rows: `36`
- Phase 5 fit-ready hydraulic rows: `12`
- Phase 5 fit-ready thermal rows: `36`

## Interpretation

This suite gives you the requested explanations and checkpoints along the way.
The packages are ordered so each later phase depends on earlier closure or
trust work rather than bypassing it.

The main unresolved blockers remain:

1. feature `K_eff` still inherits the residual `p_rgh` feature path
2. enthalpy closure remains weak for most Salt spans
3. representative boundary-layer evidence is still limited to the currently
   preserved landmark/profile context
