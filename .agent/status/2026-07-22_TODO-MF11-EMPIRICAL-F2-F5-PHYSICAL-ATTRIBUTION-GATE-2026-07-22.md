---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
  generated_at_utc: 2026-07-22T14:04:10.220341+00:00
task: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
tags:
  - status
  - MF11
  - empirical-bias
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate
---

# TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22

## Objective

Connect the strong F2/F5 empirical correction result to candidate physics
without treating empirical coefficients as closures.

## Outcome

Decision: `empirical_diagnostic_only`. Attribution rows: `6`.
Coefficient plausibility rows: `2`.
Forbidden-as-physical-closure rows: `1`.

## Changes Made

- Wrote empirical F2/F5 summary table.
- Wrote physical attribution matrix.
- Wrote coefficient-to-physics plausibility table.
- Wrote assumptions/caveats ledger and contradiction log.
- Wrote no-mutation guardrails, README, summary, status, journal, and import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py tools/analyze/test_mf11_empirical_f2_f5_physical_attribution_gate.py` passed.
- `python3.11 tools/analyze/test_mf11_empirical_f2_f5_physical_attribution_gate.py` passed.

## Guardrails

- New fitting/tuning/model selection: false.
- Validation/holdout/external-test scoring: false.
- Source/property release, coefficient admission, final score: false.
- Scheduler/solver/sampler/harvest/UQ launch: false.
- Fluid/external edit, native-output mutation, registry/admission mutation:
  false.
- Blocker-register change and generated-index refresh before closeout: false.
- Residual-internal-Nu absorption: false.
