---
task: AGENT-558
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Reviewer/Writer
status: complete
---
# UMX1 Fluid Intake Decision

Task: `AGENT-558`

I reviewed the completed external Fluid row
`impl-2026-07-20-fluid-umx1-tswfc2-smoke-followup` as read-only evidence. The
Fluid journal records commit `34af0397beadcd00e7d1f6520f01ff3946209aa9` and
successful finalization of `umx1_bracket_smoke_v1`, `tswfc2_smoke_v1`, and
`umx1_tswfc2_combined_smoke_v1`.

The key technical result is that UMX1 root handling is no longer the immediate
blocker. The durable `umx1_bracket_smoke_v1` campaign completed `12` rows across
Salt3/Salt4 and six scenarios, with `12` accepted and `0` rejected. Reviewed
segment ledgers report max absolute upcomer reservoir energy residual `0.0 W`.

The score behavior still blocks progress to a grid or admission scorecard. The
best radiation-on UMX1 baseline has all-sensor RMSE `69.693542 K`; exchange-low
and exchange-mid are worse at `70.242831 K` and `71.040740 K`. Radiation-off
rows are much worse, all above `104 K` all-sensor RMSE. The combined UMX1 plus
TSWFC2 smoke also accepts roots but has all-sensor RMSE `97.990763 K`, so the
interaction does not rescue the wall/test-section blocker.

AGENT-557 closed the bounded four-node TSWFC2 nominal scorecard as
`not_admitted_no_grid_expansion`, so TSWFC2 does not supersede UMX1. The
practical next state is therefore: keep UMX1 as the primary execution substrate
because roots now work, but do not launch a UMX1 grid from the current exchange
variants. The next agent should document or implement a new setup-only physical
candidate, source/property release gate, or upcomer onset/stratification anchor
before another smoke/scorecard.

I wrote the intake package at
`work_products/2026-07/2026-07-20/2026-07-20_umx1_fluid_intake_decision/` and
updated `operational_notes/maps/forward-predictive-model.md` with the AGENT-558
decision.
