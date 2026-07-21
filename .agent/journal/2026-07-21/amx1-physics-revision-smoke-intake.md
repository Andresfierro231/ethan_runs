---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_amx1_physics_revision_smoke_intake/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_physics_revision_smoke_v1/amx1_physics_revision_smoke_audit/amx1_physics_revision_summary.json
tags: [forward-model, thermal-modeling, amx1, physics-revision-smoke]
related:
  - .agent/status/2026-07-21_AGENT-574.md
  - imports/2026-07-21_amx1_physics_revision_smoke_intake.json
task: AGENT-574
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# AMX1 Physics-Revision Smoke Intake

## Attempted

- Claimed AGENT-574 for Ethan intake and
  `impl-2026-07-21-fluid-amx1-physics-revision-smoke` for the Fluid run.
- Added and ran Salt2-only `amx1_salt2_physics_revision_smoke_v1` with one
  disabled baseline plus upper/lower vertical-only parent-cell AMX1 `m010`
  rows.
- Summarized the Fluid audit into
  `work_products/2026-07/2026-07-21/2026-07-21_amx1_physics_revision_smoke_intake/`.

## Observed

- Fluid manifest: `3/3` rows completed `ok`.
- Audit decision: `physics_revision_smoke_complete_diagnostic_only`.
- Root/ledger gates passed for both AMX1 rows.
- No form passed the progression criterion for a separate Salt1-Salt4 bounded
  comparison.
- Both rows improved mdot/velocity and TW metrics, but still worsened
  `all_rmse_K` and `tp_rmse_K`.
- Closest form: `upper_vertical_parent_cell_m010`, with
  `max_positive_core_delta=0.0003254933205099064 K`.
- Runtime: total campaign `306.28081799999995 s`, solve time `282.748951 s`,
  max scenario duration `112.118262 s`.

## Inferred

The parent-cell exchange is a real AMX1 physics revision relative to adjacent
diffusion, but it pushes the same TP/all-probe error direction and worsens the
closest Salt2 score more than the clipped pairwise form. This makes AMX1 a weak
near-term path for unlocking the predictive wall/test-section blocker unless
new CFD structure evidence identifies a more specific axial-mixing source.

## Caveats

- This was a Salt2 diagnostic smoke, not a score grid or model-selection run.
- Salt1-Salt4 expansion was intentionally deferred.
- Diagnostic temperature targets were not used as runtime inputs.

## Next Useful Actions

1. Do not run Salt1-Salt4 for the parent-cell AMX1 form.
2. Pause AMX1 form variants unless new CFD structure evidence points to a
   specific axial-mixing source or location.
3. Shift primary effort to setup-only wall/test-section/passive-boundary
   candidates, where the remaining blocker is explicitly located.
