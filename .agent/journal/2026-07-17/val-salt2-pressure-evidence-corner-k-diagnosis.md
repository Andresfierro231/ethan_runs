---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/summary.json
  - tools/analyze/build_val_salt2_pressure_evidence_corner_k_diagnosis.py
tags: [val-salt2, pressure-evidence, corner-k, admission, handoff]
related:
  - .agent/status/2026-07-17_AGENT-503.md
  - imports/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: AGENT-503
date: 2026-07-17
role: cfd-pp/Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# val_salt2 Pressure Evidence and Corner-K Diagnosis

## Why This Exists

The user asked why the corner-K lane reports `0` fit-admitted entries and asked
to work on `val_salt2` pressure evidence. Prior packages contained the answer,
but it was spread across pressure maps, branch-admission rows, corner-K tables,
and unlock queues. This task made the answer explicit and reproducible.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/decision.json`
3. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/corner_k_gate_matrix.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/val_salt2_pressure_evidence_status.csv`

## Observed Output

- `val_salt2_pressure_evidence_status.csv` has `6` branch rows, all diagnostic
  and none admitted for ordinary `f_D`/`K` fitting.
- All six branch rows carry `blocked_material_recirculation_mask`.
- Two branch rows, `lower_leg` and `test_section_span`, carry pressure-definition
  conflict flags.
- `corner_k_failure_modes.csv` has `12` current corner rows, all diagnostic.
- All twelve corner rows have negative `K_local_centerline` after centerline
  adjacent straight-loss subtraction.
- All twelve corner rows have straight-loss subtraction ratios greater than
  one, meaning the current reference subtracts more pressure loss than the
  preserved feature pressure loss.

## Inference

The current corner-K result is not saying the physical corner coefficient is
negative. It is saying the current centerline tap/straight-reference construction
is not admissible for a fitted local component K. The apparent K values remain
useful for ranking and diagnostics, but the local-K extraction fails the
scientific gates needed for coefficient fitting.

`val_salt2` pressure evidence remains useful as an external-test pressure map
and as recirculation/pressure-basis diagnostic evidence. It is not fit evidence
for ordinary single-stream `f_D` or corner K.

## Contradictions Or Caveats

- The feature total pressure losses are positive, while local centerline K is
  negative. That is the diagnostic contradiction: the straight-loss reference is
  over-subtracting, not the physical component producing negative loss.
- The pressure map is not useless. It is only rejected for closure fitting under
  the current admission policy.
- This task did not inspect native solver fields or rerun extraction. It joined
  existing evidence and made the admission logic explicit.

## Next Useful Actions

1. Resolve the pressure basis before K fitting; do not mix unresolved static
   `p` and `p_rgh` sign-conflict rows.
2. Design taps outside recirculation and outside the hybrid upcomer/test-section
   lane when the target is an ordinary single-stream K.
3. Recompute straight-loss subtraction from a physically comparable local
   straight span.
4. Isolate local component K from reset/development and branch-apparent losses.
5. Repeat the same corner-loss QoI on a mesh family and produce GCI before any
   publication-ready fit.

## Do Not Do

- Do not use current corner-K rows as 1D closure coefficients.
- Do not fit, tune, or select models using `val_salt2`.
- Do not submit duplicate pressure-ladder jobs from this package.
- Do not mutate native OpenFOAM outputs, registry/admission state, or external
  Fluid source.
