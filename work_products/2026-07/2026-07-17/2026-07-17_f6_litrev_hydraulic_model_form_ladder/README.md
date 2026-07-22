---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/summary.json
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/untried_litrev_model_forms.csv
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/litrev_to_current_evidence_crosswalk.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard/prerequisite_gate_scorecard.csv
tags: [f6, friction, litrev, hydraulic-model-forms]
related:
  - .agent/status/2026-07-17_AGENT-512.md
  - .agent/journal/2026-07-17/f6-litrev-hydraulic-model-form-ladder.md
task: AGENT-512
date: 2026-07-17
role: Hydraulics/Literature-synthesis/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 LitRev Hydraulic Model-Form Ladder

Generated: `2026-07-17T20:44:40+00:00`

## Decision

This package ranks the hydraulic/friction model forms worth trying next. It
does not promote a closure. Anchor-first remains the research path: terminal
PM10/high-heat rows must produce admitted low-reverse pressure anchors before
ordinary F6 can be scored.

## Current Counts

- Ladder rows: `11`.
- Anchor tree rows: `6`.
- LitRev hydraulic crosswalk rows: `12`.
- Forbidden shortcut rows: `6`.
- PM5 ordinary anchors: `0`.
- PM5 recirculation diagnostics: `12`.
- Production closure: `F3_shah_apparent`.
- Promotion allowed now: `no`.

## Outputs

- `hydraulic_model_form_ladder.csv`
- `anchor_first_decision_tree.csv`
- `litrev_hydraulic_crosswalk.csv`
- `forbidden_shortcuts.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. The package is a research planning and evidence-ranking artifact,
not a CFD launch, terminal harvest, or model admission.
