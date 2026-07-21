---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [journal, hydraulics, h1, fluid-api]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
task: AGENT-326
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Fluid Localized H1 and Boundary API

Observed: Fluid had one aggregate `MinorLosses.total_fixed_k()` path. I added a
localized fixed-K map and charged local dynamic pressure inside
`distributed_and_minor_losses()`.

Inferred: this is enough to stop using one global K as the only available hook,
but it is not a faithful H1 reset/redevelopment model and it has not been run
through Salt2/Salt3/Salt4.

Validation passed for default no-op and direct/parent localized-K behavior.
Boundary/HX/wall/radiation first-class dictionaries remain open.
