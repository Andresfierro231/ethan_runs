---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [forward-model, hydraulics, h1, fluid-api]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md
task: AGENT-326
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Fluid Localized H1 and Boundary API

This lane made one bounded Fluid source change: `MinorLosses` now supports
`localized_fixed_k_by_segment`, and `distributed_and_minor_losses()` applies
that localized K using each segment's local dynamic pressure. Keys may name a
resolved segment or a parent segment; parent keys are distributed by child
parent fraction so refined and unrefined geometries preserve total K.

This is not a final H1 closure. It does not implement reset/redevelopment
semantics, does not run a calibrated Salt2/3/4 Fluid rerun, and does not create
first-class setup boundary dictionaries for HX/wall/radiation. Those remain
forward-v1 blockers.

## Validation

Passed:

```bash
python3 -m unittest tests.test_solver_contracts.SolverContractTests.test_minor_losses_default_has_no_localized_fixed_k tests.test_solver_contracts.SolverContractTests.test_minor_losses_support_direct_and_parent_localized_fixed_k
```

No native CFD solver outputs were touched.
