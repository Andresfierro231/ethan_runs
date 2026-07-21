---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/coupled_delta_vs_m3.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/runtime_input_audit.csv
tags: [journal, AGENT-514, paper-section, wall-test-section, source-shape-plan]
related:
  - .agent/status/2026-07-17_AGENT-514.md
  - AGENT-498
  - AGENT-511
  - AGENT-513
task: AGENT-514
date: 2026-07-17
role: Writer
type: journal
status: complete
---
# Paper Wall/Test-Section Coupled Score And Physics Plan

## Why

The coupled M3+test-section+cooler scorecard now has completed rows, so it can
be written as a scientific result rather than a run-status note. The important
finding is not merely that no PB2/PB3 candidate was admitted; it is that the
candidate family improves mdot while degrading temperature shape. That is a
strong constraint on the remaining wall/test-section blocker.

## Work Done

Added:

- `reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md`
- index entry in `reports/thesis_dossier/Chapters_and_sections/current/README.md`
- AGENT-514 status and import manifest.

The section records:

- AGENT-498 execution provenance (`srun` step `3299312.2`, `12/12` completed
  coupled rows, accepted roots);
- runtime-input audit boundary;
- PB2/PB3 candidate definitions at paper-safe level;
- admission gate;
- exact Salt3/Salt4 delta table versus M3;
- paper paragraph and figure/table recommendations;
- next-step plan for heater source redistribution, wall-temperature drive,
  axial mixing/upcomer exchange, and test-section wall/fluid coupling.

## Interpretation

The result should be used in a paper as diagnostic falsification evidence. It
does not close `predictive-wall-test-section-submodels`. It narrows the blocker:
passive external hA redistribution and total heat-removal magnitude are not
sufficient. Future work should target heat source placement, drive temperature,
mixing/exchange, or explicit wall/fluid coupling.

## Guardrails Preserved

- No Salt3/Salt4 fitting.
- No validation/holdout `wallHeatFlux`, mdot, wall-shell temperature, probe
  temperature, imposed cooler duty, or realized test-section heat as runtime
  inputs.
- No solver or scheduler action in this writer pass.
- No scientific admission change.
