---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/pressure_basis_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_a_pair_reconstruction_validation.csv
tags: [f6, pressure-basis, p-rgh, hydrostatic, diagnostic, no-admission]
related:
  - .agent/journal/2026-07-21/f6-static-p-basis-reconstruction-audit.md
  - imports/2026-07-21_f6_static_p_basis_reconstruction_audit.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/README.md
task: TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Reviewer / Tester / Writer
type: status
status: complete
---
# TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT Status

## Objective

Decide whether missing coarse F6 static pressure `p` can be reconstructed from
`p_rgh` with an explicit gravity/sign/reference convention validated against
rows where both fields were sampled.

## Outcome

Complete. The audit validates `p = p_rgh + rho * (g dot x)` for Stage A
pairwise pressure differences. The selected convention passes all `4/4` Stage A
pair-delta checks with max absolute error `4.38272935163 Pa`; the opposite sign
passes `0/4` and fails by up to `14051.3665823 Pa`.

The coarse Stage B static-pressure basis is now available as diagnostic
reconstruction only. F6 remains closed to component/cluster `K` admission because
ordinary-flow still fails and same-QOI mesh/UQ remains blocked.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT.md`
- `.agent/journal/2026-07-21/f6-static-p-basis-reconstruction-audit.md`
- `imports/2026-07-21_f6_static_p_basis_reconstruction_audit.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/build_f6_static_p_basis_reconstruction_audit.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/test_f6_static_p_basis_reconstruction_audit.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/pressure_basis_source_inventory.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_a_reconstruction_validation.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_a_pair_reconstruction_validation.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_b_static_p_reconstruction_decision.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_b_pair_reconstructed_static_deltas.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/pressure_basis_decision.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/admission_impact.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json`

## Validation

- `python3.11 tools/agent/preflight_task.py --task-id TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT` initially failed after a broad `tools/analyze/` claim was proposed; the board row was narrowed to package-local scripts.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT` passed after the scope correction.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/build_f6_static_p_basis_reconstruction_audit.py work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/test_f6_static_p_basis_reconstruction_audit.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/test_f6_static_p_basis_reconstruction_audit.py` passed with 5 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing launch, Fluid/external
edit, fitting/tuning/model selection, coefficient admission, clipped `K`, hidden
global multiplier, blocker-register change, generated-index refresh, or
`tools/analyze/**` edit was performed.

Next useful row: `TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE`, using this audit
as diagnostic static-pressure-basis evidence and preserving no-admission
language.
