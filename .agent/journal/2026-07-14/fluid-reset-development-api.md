---
task: AGENT-361
date: 2026-07-14
role: Hydraulics / Fluid API / Implementer / Tester / Writer
status: complete
---
# Fluid Reset/Development API

Implemented the HYD-RESET-API slice as a narrow external Fluid edit. The API now
accepts reset/development K values separately from localized fixed K:

- `MinorLosses.reset_development_k_by_segment`
- `MinorLosses.reset_development_k_for_segment(segment)`
- `campaigns.yaml` minor-loss preset key `reset_development_k_by_segment`

The solver adds this term separately in `distributed_and_minor_losses`, using
`K * 0.5 * rho * v^2` for each segment. Parent-segment keys follow the same
refined-geometry fraction behavior as localized fixed K.

This closes the immediate API separation gap, but not the scientific admission
gate. H1 remains blocked until pressure evidence admits reset/development and
component/cluster K terms. No thermal fitting, native CFD mutation, scheduler
action, or global multiplier was used.
