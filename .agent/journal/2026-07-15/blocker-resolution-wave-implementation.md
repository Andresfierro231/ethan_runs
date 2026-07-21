---
provenance:
  task: AGENT-413
  generated_by: codex
tags: [journal, blockers, forward-v1, fluid-api, thermal-admission, f6]
related:
  - .agent/status/2026-07-15_AGENT-413.md
  - work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/README.md
---
# Blocker Resolution Wave Implementation

2026-07-15T09:31:00-05:00 - Claimed AGENT-413 to implement the broad blocker
wave while avoiding active AGENT-411/412 scopes. Scheduler remained read-only
and native CFD outputs remained immutable.

2026-07-15T09:38:00-05:00 - Added a direct Fluid `hx_ua_multiplier` to the
predictive air-side HX path. The scalar multiplies UA inside
`_hx_airside_transfer`; default `1.0` preserves baseline behavior and does not
pass imposed CFD cooler duty as runtime input.

2026-07-15T09:42:00-05:00 - Built the AGENT-413 evidence package. The current
PM5 rows are now F6/onset-review-ready (`12/12`) but not admitted. Thermal
internal-Nu remains blocked with `0` fit-admissible rows; current reviewed rows
are validation-only or blocked.

2026-07-15T09:46:00-05:00 - Refreshed the curated blocker register and generated
indexes. The old Fluid external-boundary API blocker is resolved/recast:
external-boundary dictionaries exist and HX UA multiplier exists; the remaining
work is setup-only scorecard validation and admission under the predictive
heater/cooler/wall submodel blocker.

## Remaining Work

1. Run the PM5/F6 onset scorecard over AGENT-406 rows.
2. Resolve thermal sign/heat-balance/downcomer policy before any internal-Nu fit.
3. Fit and score `hx_ua_multiplier` on Salt2/Salt3/Salt4 split without refit.
4. Admit or reject raw two-tap pressure evidence before final hydraulic residual
   attribution.
5. Rebuild final forward-v1 only from admitted rows.
