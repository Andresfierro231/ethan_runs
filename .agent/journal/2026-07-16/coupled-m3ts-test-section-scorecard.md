---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/blocker_decision.json
tags: [forward-model, m3ts, test-section, fluid]
related:
  - .agent/status/2026-07-16_AGENT-461.md
  - .agent/blockers.yml
task: AGENT-461
date: 2026-07-16
role: Coordinator/BC-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Coupled M3+TS Test-Section Scorecard

## Observed

The prior AGENT-458 screen was blocked by the absence of a coupled solver path
for a physical test-section loss. AGENT-461 added the missing Fluid interface:
`external_boundary_role_rows` can now replace a targeted parent segment's
external-boundary loss with a sum of setup-only role rows. This is the correct
shape for the upcomer because the quartz test section is a subspan role on
`left_upper_vertical`, not a separate ordinary parent segment.

The Ethan builder produced 9 role-boundary scenario rows for three candidates
over Salt2/Salt3/Salt4 and preserved M2/M3 diagnostic comparators. Runtime audit
passes for the scenario contracts.

## Inferred

The blocker is narrowed again. It is no longer accurate to say Fluid cannot
represent the test-section subspan. The remaining open gate is execution and
admission of the coupled M3+TS score on a compute node.

## Blocker Action

`.agent/blockers.yml` still keeps `predictive-wall-test-section-submodels` open.
Resolution now requires running:

```bash
python3 tools/analyze/build_coupled_m3ts_test_section_scorecard.py --run-fluid
```

on a compute node and admitting a candidate only if runtime, heat-loss, and
coupled mdot/TP/TW gates all pass.

## Guardrails

Do not use realized CFD wallHeatFlux, realized CFD test-section heat, CFD mdot,
imposed CFD cooler duty, or validation/holdout temperatures as runtime inputs.
