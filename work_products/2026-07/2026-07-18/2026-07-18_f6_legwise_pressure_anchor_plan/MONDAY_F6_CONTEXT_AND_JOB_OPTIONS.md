---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
tags: [pressure-ledger, friction-closures, f6, monday-handoff, scheduler]
related:
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/README.md
  - operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md
  - operational_notes/07-26/17/2026-07-17_MONDAY_MORNING_FRESH_AGENT_HANDOFF.md
task: AGENT-547
date: 2026-07-18
role: Hydraulics/Writer
type: operational_note
status: complete
---
# Monday F6 Context And Job Options

This note records the continuation context after AGENT-547. It is F6/pressure
specific and should be read after the standard startup files and the current
board.

## Current Context

The legwise F6 package made progress by separating pressure evidence by leg and
use mode. Current finite endpoint evidence is not an ordinary F6 anchor: the
three `corner_lower_right` endpoint pairs have finite pressure/velocity fields,
but all three fail material reverse-flow gates. The current F6 state is
therefore:

- 3 finite raw endpoint feature pairs.
- 3 finite endpoint pairs blocked by material reverse flow.
- 0 ordinary F6 fit-eligible rows.
- 0 admission-review eligible rows.
- Future review baseline: `F3_shah_apparent`.
- Required guardrail: no hidden global multiplier.

Do not assume recirculation is limited to the upcomer. The upcomer should be a
separate throughflow-plus-recirculation pressure-closure lane, while ordinary
F6 needs low-reverse straight-leg pressure anchors.

## Scheduler Snapshot

Read-only scheduler check on Saturday, 2026-07-18 showed:

| job | state | role |
| --- | --- | --- |
| `3293924` | RUNNING | corrected Salt2/Salt4 selected-Q continuation |
| `3295438` | PENDING dependency | selected-Q harvester waiting on `3293924` |
| `3299610` | RUNNING | Salt4 Q3x no-recirculation probe |
| `3299620` | RUNNING | Salt4 high-heat pack |
| `3302317` | RUNNING | dev/Fluid-side active work |

## Weekend Launch Decision

Do not launch a new F6/pressure solver or harvester before Monday from this
context. The useful long-running CFD jobs are already active or
dependency-held. Launching duplicates would create provenance and admission
conflicts.

## Conditional Monday Job Options

1. Corrected-Q selected harvest/admission
   - Launch only if `3293924` is terminal and `3295438` has either completed
     successfully or is absent for a documented reason.
   - Purpose: admit or reject Salt2/Salt4 +/-10Q future holdout rows.
   - Guardrail: do not use these as fit rows by default.

2. Salt4 high-heat/no-recirculation harvest
   - Launch only after `3299610` or `3299620` is terminal successful and logs
     show usable outputs.
   - Purpose: test low-reverse/upcomer-onset/F6-anchor gates.
   - Guardrail: claim a fresh cfd-pp/admission row before parsing or scoring.

3. Nonrecirculating pressure-anchor sampler
   - Launch only after a candidate case/feature passes preflight or is selected
     from the high-heat terminal harvest.
   - Minimum acceptance: exact endpoint labels, finite `p`, `p_rgh`, `U`, `rho`
     or `T`, face area/normal, RAF/RMF/SVF, and same-QOI UQ plan.
   - Guardrail: no F6 fit or component-K admission from raw samples alone.

4. TSWFC2 or UMX1 Fluid score grid
   - Launch only after the active external Fluid row releases the target files
     and dry/smoke gates pass.
   - Purpose: forward-predictive model screening, not hydraulic admission.
   - Guardrail: no runtime leakage of validation temperatures, realized CFD
     wall heat flux, or realized CFD mdot.

5. Salt3 Q x insulation onset anchors
   - Launch only after Salt4 high-heat jobs reach terminal review and a new
     board row claims staging/scheduler authority.
   - Priority candidates from the existing design are the Salt3 150 W low-ins,
     1500 W high-ins sentinel pair, then the 250/500/1000 W small matrix.
   - Guardrail: these are onset anchors and cannot become ordinary upcomer
     Nu/f_D/K fits unless reverse-flow gates pass.

## Next Steps Without New Launches

- Refresh `squeue` and `sacct` Monday before any scheduler action.
- Let AGENT-519 or a successor monitor hand off terminal jobs; do not harvest
  from a read-only monitor row.
- If no terminal harvest is ready, prioritize source/property gate
  infrastructure, scorecard templates, and F6/pressure admission-contract
  checks because they are low-cost and reduce thesis risk.
