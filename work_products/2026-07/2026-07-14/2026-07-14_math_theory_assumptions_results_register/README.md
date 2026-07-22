---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [thesis-source, methodology, equations, assumptions, results-contract, forward-model]
related:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-322
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Math, Theory, Assumptions, and Results Register

This package is the cross-cutting documentation contract for the CFD-to-1D
closure workflow. It records the equations that future packages should cite,
the assumptions that protect predictive-mode hygiene, and the fields required
when new results arrive.

## Purpose

The project should not progress by tuning one global coefficient. Each result
must state its governing balance, property lane, fitted parameters, split role,
admission status, and overclaim boundary. This package makes that requirement
machine-readable enough for future builders and human-readable enough for the
thesis methods chapter.

## Files

- `equation_register.csv`: `16` equations/definitions and
  their allowed/blocked use.
- `assumption_register.csv`: `7` assumptions and
  violation conditions.
- `result_intake_contract.csv`: `17` required fields
  for future scorecards and gate packages.
- `current_evidence_hooks.csv`: current result hooks that future agents should
  update or cite as gates move.
- `summary.json`: machine-readable package metadata.

## Current Interpretation

- Forward-v0 solve_case execution is admitted as confirmation evidence.
- H1 is useful hydraulic directionality evidence, but remains proxy-only until
  localized named-loss/reset support lands.
- Thermal UA/HTC/Nu remains blocked for fitting: the current mesh gate reports
  zero fit-admissible thermal rows.
- HX/cooler and external-boundary work must become setup-only before final
  forward-v1 can be claimed.
- Sensor temperatures are validation targets only and join after solve.

## How To Use This Register

Every new gate-moving result should cite equation IDs from
`equation_register.csv`, fill the fields in `result_intake_contract.csv`, and
state which assumptions from `assumption_register.csv` it relies on. If a result
cannot satisfy the contract, it should be labeled diagnostic-only or blocked
rather than silently excluded.
