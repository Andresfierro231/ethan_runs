---
task: TODO-PASSIVE-H2-SALT2-SAME-QOI-SETUP-UQ-GATE-2026-07-22
provenance:
  generated_by: tools/analyze/build_passive_h2_salt2_same_qoi_setup_uq_gate.py
tags: [journal, PASSIVE-H2, Salt2, same-QOI-UQ]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate/qoi_readiness_gate.csv
---
# PASSIVE-H2 Salt2 Same-QOI Setup-UQ Gate

## Attempted

Consumed the completed role/subspan recovery UQ tables and rebuilt a strict
same-QOI setup-UQ gate for Salt2.

## Observed

Six QOI labels have target/minus/plus availability. Existing perturbation
rows are finite enough for diagnostic train-context sensitivity. No QOI label
is admission-release-ready.

## Inferred

The same-QOI blocker has moved from missing diagnostic sensitivity to
diagnostic-only sensitivity. It still cannot support release or final form
without source/property and release-grade subspan gates.

## Next Useful Actions

Rerun the PASSIVE-H2 candidate source/property gate using this diagnostic UQ
and the subspan recovery row. Keep protected scoring closed.
