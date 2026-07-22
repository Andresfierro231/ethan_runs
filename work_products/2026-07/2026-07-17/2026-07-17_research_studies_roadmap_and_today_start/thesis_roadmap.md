---
provenance:
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/hydraulic_model_form_ladder.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/summary.json
  - .agent/blockers.yml
tags: [research-roadmap, thesis-roadmap, closure-ledger, forward-model]
related:
  - work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start/study_priority_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start/multi_agent_campaign_sequence.csv
task: AGENT-518
date: 2026-07-17
role: Coordinator/Writer
type: work_product
status: complete
---
# Thesis Research Roadmap

Generated: `2026-07-17T21:00:46+00:00`

## Thesis Use

The research program should be presented as a branchwise closure-ledger workflow,
not a search for one fitted coefficient. The current open blockers are
`predictive-wall-test-section-submodels`, `upcomer-onset-data-sparsity`, and
`f6-friction-re-correction`. Each study below either resolves one of those
blockers, protects the model from an invalid closure promotion, or produces a
chapter-ready limitation/future-work artifact.

## Study-To-Thesis Map

| Rank | Study | Lane | Thesis value |
| --- | --- | --- | --- |
| 1 | `terminal_anchor_and_f6_gate` | hydraulic_f6 | decides whether ordinary F6 is admissible or recirculation-mode closure is required |
| 2 | `source_envelope_refresh` | litrev_gate | chapter-ready table linking literature validity to TAMU operating space |
| 3 | `property_mode_carryforward` | litrev_gate | defensible uncertainty axis for all hydraulic and thermal claims |
| 4 | `reset_development_and_named_pressure` | hydraulic_pressure | replaces global friction tuning with a branchwise pressure ledger |
| 5 | `cfd_validity_on_every_reduction` | cfd_admission | separates single-stream closure rows from section-effective diagnostics |
| 6 | `wall_temperature_shape_physics` | thermal_wall | explains why mdot can improve while TP/TW fields regress |
| 7 | `heat_loss_separation_and_radiation_bound` | thermal_boundary | prevents internal HTC from absorbing jacket/passive/radiation residuals |
| 8 | `conditional_internal_htc_bakeoff` | thermal_internal_htc | shows why Nu forms are gated rather than tuned |

## Chapter Contributions

- Literature/method chapter: source-envelope, property-mode, reset/development,
  heat-loss separation, and CFD-validity gates show why the model uses a
  branchwise ledger instead of global `f`, `Nu`, `K`, or `UA`.
- Hydraulic chapter: terminal anchor harvest, F6 `phi(Re)`, reset-distance, and
  named-loss studies decide whether the pressure model can move beyond
  `F3_shah_apparent`.
- Thermal chapter: wall/test-section temperature-shape, heat-loss/radiation,
  and conditional HTC studies separate source placement, passive loss, and
  internal heat transfer.
- Predictive chapter: the campaign sequence preserves runtime legality and
  canonical split discipline before any corrected freeze or final scorecard.
- Future-work chapter: pressure taps, thermal instrumentation, and ROM archive
  design are framed as planned evidence pathways, not current validation.

## Claims Not Yet Allowed

- No ordinary F6 closure from PM5 rows.
- No universal fitting `K`, hidden global friction multiplier, or global `Nu`.
- No internal HTC adjustment that absorbs jacket, passive, radiation, wall, or
  source-placement residuals.
- No final predictive claim until the wall/test-section blocker and final
  scorecard gates clear.
- No ROM prediction claim until stable full-order outputs, snapshots, and
  withheld validation exist.
