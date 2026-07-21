---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_memo.md
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/outputs/coarse/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv
  - work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/outputs/medium/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/thermal_sign_enthalpy_review.csv
  - work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/closure_qoi_admission_decisions.csv
tags: [mesh-gci, thermal-closure, uncertainty, gci]
related:
  - .agent/status/2026-07-14_AGENT-309.md
  - imports/2026-07-14_thermal_closure_mesh_gate_refresh.json
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-309
date: 2026-07-14
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Thermal / Closure Mesh Gate Refresh

## Context

The July 13 thermal gate still reported missing coarse thermal triplets. After
AGENT-305's Salt2 coarse thermal repair smoke completed, I refreshed the gate
instead of treating the smoke as admission. This keeps the source-row question
separate from closure use.

## Implemented

Updated `tools/analyze/build_thermal_mesh_gate.py` so it now consumes:

- coarse thermal repair-smoke segment CSV;
- medium reconstructed-T repair trial segment CSV;
- fine reconstructed-T repair trial segment CSV;
- prior nonthermal closure-QOI mesh/GCI decision package;
- sign/enthalpy review rows;
- physical-interface enthalpy residual rows.

The builder writes a July 14 package at
`work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/`.
The main table is
`refreshed_qoi_mesh_gate_status.csv`, which records coarse/medium/fine
availability, classification, blockers, and exact source paths for each row.
The Agent-3-facing table is `thermal_admission_table.csv`, and the compact
memo is `thermal_admission_memo.md`.

## Observed

Coarse, medium, and fine thermal values now exist for lower-leg HTC/UA and
upcomer HTC/UA/Nu. Lower-leg Nu remains missing/nonfinite and direct Nu is not
admitted. Downcomer/right-leg remains policy-blocked at all three levels.

The refreshed classification counts are:

- `publication-ready GCI`: `0`
- `diagnostic-only`: `0`
- `blocked-sign-review`: `5`
- `blocked-downcomer-policy`: `1`
- `blocked-missing-triplet`: `5`
- `non-monotone/oscillatory`: `14`

The admission table has `16` lower-leg/upcomer/downcomer rows. Fit-eligible
rows are `0`; validation-only diagnostic rows are `11`; blocked rows are `5`.

- Lower-leg: wallHeatFlux, enthalpy change, segment duty, HTC, and UA_prime are
  validation-only. Nu is blocked because the triplet is missing/nonfinite and
  direct Nu is not admitted.
- Upcomer: wallHeatFlux, enthalpy change, segment duty, HTC, UA_prime, and Nu
  are validation-only recirculation/heat-balance diagnostics. They are not fit
  targets because wallHeatFlux and enthalpy oppose, the residual is large, and
  interfaces are high-recirculation.
- Downcomer/right-leg: all rows are blocked by downcomer policy, opposed
  wallHeatFlux/enthalpy direction, large residual, and high-recirculation
  interface flags.

## Interpretation

No thermal or closure QOI is publication-ready. The coarse smoke is useful
diagnostic evidence that the extraction path can produce triplets for some
thermal quantities, but every finite thermal triplet is still blocked by the
wallHeatFlux/enthalpy sign review. Nonthermal closure rows remain blocked by
missing triplets or non-monotone/oscillatory mesh behavior.

Sign convention used for admission: positive wallHeatFlux / segment duty heats
the fluid, positive enthalpy change means bulk fluid enthalpy increases across
the declared interfaces, and HTC/UA/Nu are positive effective transfer
magnitudes rather than heat-source directions. CFD `rcExternalTemperature`
includes radiation in total `wallHeatFlux`; there is no separate exported `qr`
term, so radiation must not be fit back into internal Nu.

The refresh intentionally leaves GCI bands blank for two-level, blocked,
oscillatory, or divergent rows. Convergence verdicts are reported separately
where triplets are complete.

## Validation

- `python3.11 -m unittest tools.analyze.test_thermal_mesh_gate`
- `python3.11 -m py_compile tools/analyze/build_thermal_mesh_gate.py tools/analyze/test_thermal_mesh_gate.py`
- `python3.11 tools/analyze/build_thermal_mesh_gate.py`
- `python3.11 -m json.tool work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/summary.json`

## Next

The next useful task is a thermal sign/enthalpy/heat-balance admission review.
It should decide whether the lower-leg and upcomer triplets can be admitted as
thermal source rows, and separately whether downcomer/right-leg should remain
excluded.
