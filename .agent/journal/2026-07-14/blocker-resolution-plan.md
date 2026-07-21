---
provenance:
  - .agent/BLOCKERS.md
  - .agent/STATE.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/README.md
tags: [journal, blocker-register, coordination, scientific-rigor, forward-model, thermal-closure, friction]
related:
  - .agent/status/2026-07-14_AGENT-323.md
  - imports/2026-07-14_blocker_resolution_plan.json
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-323
date: 2026-07-14
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
---
# Blocker Resolution Plan

## Objective

Turn the current open blockers into three concrete, scientifically defensible
progress areas with work packets, acceptance gates, source paths, and
documentation contracts.

## Three Major Areas

1. **Thermal admission, mesh GCI, and internal Nu** — resolve sign,
   heat-balance, lower-leg Nu, and downcomer policy before thermal fitting or
   publication GCI.
2. **Forward predictive model and boundary/HX submodels** — replace
   diagnostic replay/proxy inputs with setup-only heater, cooler/HX, wall, and
   boundary candidates under the locked split.
3. **Hydraulic closure, recirculation physics, and API/model-form gaps** —
   decide H1/F6 paths, expand upcomer onset evidence, and define the Fluid
   external-boundary handoff without hiding losses in a global multiplier.

## Scientific Controls

- Every open blocker has at least one work packet in
  `blocker_coverage.csv`.
- No GCI is allowed for two-level, blocked-source, non-monotone, oscillatory,
  divergent, or source-unadmitted rows.
- Repair-smoke thermal outputs remain diagnostic unless a later admission gate
  explicitly admits them.
- CFD `wallHeatFlux` is treated as already including
  `rcExternalTemperature` radiation; no separate 1D radiation term is added
  when using those totals.
- Predictive runs must not use CFD mdot, realized CFD `wallHeatFlux`, or
  validation temperatures as runtime inputs.
- The stale blockers for OF13 reconstruction, missing mesh families, and CFD
  radiation parity are excluded from active packet targets.

## Files Created

- `tools/analyze/build_blocker_resolution_plan.py`
- `tools/analyze/test_blocker_resolution_plan.py`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/blocker_resolution_areas.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/work_packets.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/scientific_rigor_checklist.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/milestone_sequence.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/blocker_coverage.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/source_manifest.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/summary.json`

## Validation

- `python3.11 -m unittest tools.analyze.test_blocker_resolution_plan`
- `python3.11 -m py_compile tools/analyze/build_blocker_resolution_plan.py tools/analyze/test_blocker_resolution_plan.py`
- `python3.11 tools/analyze/build_blocker_resolution_plan.py`

## Next Action

Start with packet `A1.1` (thermal sign and heat-balance admission review), then
run the hydraulic/API and setup-only boundary packets in parallel where active
board scopes allow it. Do not mark any blocker resolved until a later package
satisfies its acceptance gate and updates the blocker register with evidence.
