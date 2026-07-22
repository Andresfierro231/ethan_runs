---
provenance:
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/hydraulic_model_form_ladder.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/summary.json
  - .agent/blockers.yml
tags: [research-roadmap, closure-ledger, thesis-roadmap, forward-model]
related:
  - .agent/status/2026-07-17_AGENT-518.md
  - .agent/journal/2026-07-17/research-studies-roadmap-and-today-start.md
task: AGENT-518
date: 2026-07-17
role: Coordinator/Writer/Implementer/Tester
type: work_product
status: complete
---
# Research Studies Roadmap And Today-Start Package

Generated: `2026-07-17T21:00:46+00:00`

## Decision

The highest-value studies are gate/ledger studies that make future closure
claims identifiable: terminal anchor harvest, source envelope, property-mode
carryforward, reset/named pressure losses, CFD validity diagnostics, wall
temperature-shape physics, heat-loss/radiation separation, and conditional HTC.
This package does not launch jobs or promote any model.

## Outputs

- `study_priority_matrix.csv`
- `today_start_ledger.csv`
- `multi_agent_campaign_sequence.csv`
- `thesis_roadmap.md`
- `handoff_tomorrow.md`
- `source_manifest.csv`
- `summary.json`

## Current Counts

- Study rows: `10`.
- Today-start rows: `6`.
- Campaign waves: `6`.
- Open blockers preserved: `f6-friction-re-correction, predictive-wall-test-section-submodels, upcomer-onset-data-sparsity`.
- PM5 ordinary F6 scoreable rows: `0`.
- PM5 recirculation diagnostic rows: `12`.
- Segment pressure fit-admitted rows: `0`.
- Residual internal-Nu fit-admitted rows: `0`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, thesis-dossier files, or active-agent scoped
artifacts were mutated. This is a planning and synthesis package, not a solver
run, postprocessing harvest, model fit, or scientific admission change.
