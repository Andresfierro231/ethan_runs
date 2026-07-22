---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_final_reverse_flow_switching_calibration_design/README.md
tags: [journal, reverse-flow, switching]
related:
  - .agent/status/2026-07-22_TODO-1D-FINAL-REVERSE-FLOW-SWITCHING-CALIBRATION-DESIGN-2026-07-22.md
task: TODO-1D-FINAL-REVERSE-FLOW-SWITCHING-CALIBRATION-DESIGN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Forward-pred / Writer / Reviewer / Tester
type: journal
status: complete
---
# 1D Reverse-Flow Switching Calibration Design

## Attempted

Converted the dry recirculation switch contract and LitRev UC-03 requirements
into a calibration design with topology states, metrics, missing inputs, and
activation gates.

## Observed

Current evidence supports a diagnostic signed-flow lane, but not one-stream
ordinary upcomer closure or exchange-cell coefficient admission.

## Inferred

The future switch needs topology labels and false-positive/false-negative
controls before any coefficient can be fit. Current evidence is useful for
design, not admission.

## Next Useful Actions

Run a topology-label audit, wait for pressure endpoint readiness, complete S13
same-QOI exchange GCI, then run a train/support-only switching smoke before
freeze.
