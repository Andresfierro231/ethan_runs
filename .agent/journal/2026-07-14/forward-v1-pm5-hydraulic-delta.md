---
date: 2026-07-14
task: AGENT-362
title: Forward-v1 +/-5Q and hydraulic tap-length delta
tags:
  - journal
  - forward-model
  - corrected-q
  - hydraulics
  - scorecard
related:
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/README.md
---

# Forward-v1 +/-5Q and hydraulic tap-length delta

Decision: forward-v1 remains blocked. The landed +/-5Q corrected-Q and hydraulic
tap-length evidence moves the scorecard closer to rerun readiness, but does not
admit a final scorecard.

Admitted progress:

- Four corrected-Q +/-5Q rows are terminal-harvested and closure-fit-admissible
  under the current terminal gate: `salt2_lo5q`, `salt2_hi5q`, `salt4_lo5q`,
  and `salt4_hi5q`.
- Those rows provide sensitivity/admission evidence only. They add zero
  independent train/validation/holdout rows until a dated perturbation split
  policy admits them.
- The heat-role reductions for the four rows are now citeable score targets:
  cooling-branch total removal spans 129.533202767 W to 177.688156227 W.
- The hydraulic tap-length refresh resolved 12 preserved corner rows with
  mesh-centerline station lengths and left 3 test-section connector rows
  blocked on raw two-tap extraction.

Still not admitted:

- No component/cluster K rows are fit-admissible after the tap-length refresh.
- H1 is still not faithfully launchable.
- +/-5Q rows cannot silently expand the training set.
- H1 proxy, imposed cooler duty, diagnostic thermal rows, diagnostic internal
  Nu rows, and diagnostic upcomer recirculation evidence remain non-final
  predictive evidence.

Next gate actions:

- Harvest AGENT-357/AGENT-363 matched pressure/upcomer metrics when their
  outputs land.
- Write a dated perturbation split policy before any +/-5Q row can alter the
  train/validation/holdout population.
- Recompute F6/onset hydraulics only after admitted Re-variation metrics exist.
- Convert boundary/HX evidence into setup-only score targets, not CFD-duty
  runtime inputs.
- Refresh the forward-v1 gate delta only after cfd-pp, hydraulics, and
  BC-modeling gates land.

No native CFD outputs, registry/admission files, scheduler state, or external
Fluid source files were changed by this task.
