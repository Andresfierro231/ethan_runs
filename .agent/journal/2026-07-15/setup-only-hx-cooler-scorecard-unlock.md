---
provenance:
  task: AGENT-438
  generated_by: codex
tags: [journal, forward-v1, hx, cooler, setup-only]
related:
  - .agent/status/2026-07-15_AGENT-438.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/README.md
---
# Setup-Only HX/Cooler Scorecard Unlock

Date: 2026-07-15
Task: AGENT-438

This task executed the next non-mutating unlock step after the recirculation
policy package. It did not run Fluid, OpenFOAM, or scheduler jobs. Instead it
consolidated the already-landed setup-only HX/cooler score evidence into a
single gate artifact.

The preferred candidate is `salt2_fit_constant_UA_bulk_drive`. It fits the
scalar on Salt2, validates on Salt3, and holds out Salt4 without refit. The
candidate passes the AGENT-438 screen:

- validation error <= `5 W`
- holdout error <= `10 W`
- runtime input violation count equals zero

The target cooler duty is used only for scoring:

`error_W = abs(predicted_qhx_W - target_qhx_W_for_scoring_only)`

The result advances HX/cooler modeling as a setup-only candidate input to a
future final forward-v1 scorecard. It does not make final forward-v1 admissible.
The remaining hard blockers are hydraulic pressure/F6 admission, internal-Nu
or thermal residual ownership/sign/heat-balance admission, recirculation
model-form policy, and mesh/GCI/UQ.

No native CFD outputs, scheduler state, registry/admission state, generated
indexes, or external Fluid files were mutated.
