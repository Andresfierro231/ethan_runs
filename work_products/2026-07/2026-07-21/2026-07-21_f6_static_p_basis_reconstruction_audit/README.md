---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_face_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/stage_a_endpoint_face_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/stage_b_coarse_endpoint_face_matrix.csv
  - operational_notes/maps/pressure-and-momentum-budget.md
tags: [f6, pressure-basis, p-rgh, hydrostatic, diagnostic, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/README.md
task: TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Reviewer / Tester / Writer
type: work_product
status: complete
---
# F6 Static Pressure Basis Reconstruction Audit

This package tests whether coarse F6 static pressure can be reconstructed from
`p_rgh` for diagnostic same-QOI pressure evidence.

Open first:

1. `pressure_basis_decision.csv`
2. `stage_a_pair_reconstruction_validation.csv`
3. `stage_b_pair_reconstructed_static_deltas.csv`
4. `admission_impact.csv`
5. `summary.json`

## Finding

The Stage A validation rows support the OpenFOAM-style basis
`p = p_rgh + rho * (g dot x)` for pairwise pressure differences. The plus
convention passes all `4/4` Stage A pair-delta checks with max absolute error
`4.38272935163 Pa`; the opposite sign passes `0/4` and has max absolute error
`14051.3665823 Pa`.

The coarse Stage B rows are therefore reconstructed as diagnostic-only static
pressure evidence. Reconstructed coarse pair deltas are:

| case | branch | reconstructed delta p static Pa |
| --- | --- | ---: |
| salt_2 | right_leg | -7022.2752359 |
| salt_2 | test_section_span | 1882.80775068 |
| salt_3 | right_leg | -6986.51809335 |
| salt_3 | test_section_span | 1873.25558957 |
| salt_4 | right_leg | -6945.13826285 |
| salt_4 | test_section_span | 1862.23627355 |

## Interpretation

This resolves the missing coarse static-`p` basis for diagnostic pressure
comparisons, but it does not admit F6 or any component/cluster `K`. The Stage B
gate refresh still has `0/10` endpoint pairs passing the ordinary-flow RAF/RMF
gate, and same-QOI mesh/UQ remains blocked. Pressure increases around corners
must still be labeled as hydrostatic/recovery/section-effective/diagnostic
terms rather than clipped into negative loss.

## Reproduction

Run from the repo root:

```bash
python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/test_f6_static_p_basis_reconstruction_audit.py
```

The test regenerates the package outputs and checks row counts, sign-convention
selection, Stage B diagnostic-only reconstruction, and the no-admission
guardrails.

## Guardrails

No native OpenFOAM files, registry/admission state, scheduler jobs, Fluid source
tree, external repos, blocker register, or generated documentation indexes were
mutated. No clipped `K`, global multiplier, F6 fit, component `K`, or cluster
`K` was produced.
