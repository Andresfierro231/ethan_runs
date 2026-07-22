---
provenance:
  - .agent/BLOCKERS.md
  - .agent/STATE.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [blocker-register, coordination, forward-model, thermal-closure, friction, uncertainty]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-323
date: 2026-07-14
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Blocker Resolution Plan

Generated: `2026-07-14T11:41:50-05:00`

## Purpose

This package turns the current open blockers into a scoped, testable research
plan. It is designed to drive gate-moving work with scientific rigor: every
work packet has source provenance, acceptance gates, failure modes, and a
documentation contract.

## Three Major Areas

1. **Thermal admission, mesh GCI, and internal Nu**: resolve sign, heat-balance,
   lower-leg Nu, and downcomer policy before any thermal fit or GCI claim.
2. **Forward predictive model and boundary/HX submodels**: move from
   diagnostic replay/proxy evidence toward setup-only predictive runs under the
   locked split.
3. **Hydraulic closure, recirculation physics, and API/model-form gaps**:
   decide H1/F6 paths, expand upcomer recirculation evidence, and prepare the
   first-class external-boundary API handoff.

## Current Counts

- Open blockers covered: `6` / `6`
- Work packets: `9`
- Rigor gates: `10`
- Milestones: `5`
- Plan validation errors: `0`

## Outputs

- `blocker_resolution_areas.csv`: the three major areas and their blocker map.
- `work_packets.csv`: ordered execution packets with acceptance gates.
- `scientific_rigor_checklist.csv`: non-negotiable scientific guardrails.
- `milestone_sequence.csv`: dependency-ordered milestone plan.
- `blocker_coverage.csv`: proof every open blocker has a work packet.
- `source_manifest.csv`: source paths validated by the builder.
- `summary.json`: machine-readable counts and validation result.

## Immediate Execution Order

1. `A1.1` thermal sign and heat-balance admission review.
2. `A2.1` faithful localized H1 hydraulic implementation or rejection.
3. `A2.2` setup-only cooler/HX and heater boundary candidate.
4. `A3.1` bounded F6 Re-dependent friction screen.
5. `A3.2` upcomer recirculation onset evidence expansion.

## Interpretation Boundary

This package does not resolve the blockers by assertion. It makes them
actionable and testable. A blocker should only be marked resolved or superseded
after a later package satisfies the acceptance gate and updates
`.agent/blockers.yml` with evidence.
