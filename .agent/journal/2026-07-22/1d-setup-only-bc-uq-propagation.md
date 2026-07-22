---
provenance:
  - tools/analyze/build_1d_setup_only_bc_uq_propagation.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/uncertainty_source_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/protected_row_guardrails.csv
task: TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22
date: 2026-07-22
role: Uncertainty / Forward-pred / Thermal-modeling / Hydraulics / Tester / Writer
type: journal
status: complete
tags: [journal, predictive-1d, uncertainty, setup-only, no-admission]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation
  - .agent/status/2026-07-22_TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22.md
---
# 1D Setup-Only BC UQ Propagation

## Attempted

Claimed the setup-only BC UQ row and built a contract package from the forward
predictive map, conservative thermal ledger, sensor projection operator,
heat-loss Phase 0/1 packages, source/property enforcement, and MF02 pressure
diagnostic. Added a focused builder/test pair and generated UQ source, plan,
sensitivity, guardrail, readiness, source-manifest, and summary tables.

## Observed

The available evidence is ready for UQ planning but not UQ execution. It
supports setup-screening priors for heater distribution, cooler/HX strength,
ambient/radiation fields, external hA, wall/layer materials, property mode,
pressure losses, and sensor projection. It does not support final uncertainty
intervals or protected-row score propagation because no frozen runtime-legal
candidate exists.

## Inferred

The next efficient scientific step is a train-only one-at-a-time smoke/UQ row
that varies only setup-allowed inputs and records mdot, heat-ledger residual
owners, and TP/TW projections. Model selection must remain blocked until a
separate source/property row releases exactly one candidate.

## Contradictions or Caveats

Several ranges are intentionally broad screening priors. They are useful for
ranking sensitivity and finding which setup fields matter, but they must not be
quoted as final experimental or model uncertainty. Radiation and wall/layer
material intervals need setup/capability review before becoming publication
intervals.

## Next Useful Actions

1. Create a train-only UQ smoke row that executes the `propagation_plan.csv`
   P0-P2 stages with no protected scoring.
2. Use this package in `TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22`
   to explain why final predictive scores remain zero until freeze.
3. Keep S11/S15/S6 blocked until one source-bounded candidate is released with
   source/property labels and same-QOI UQ.
