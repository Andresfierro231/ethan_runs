# Thermal Mesh Gate

Task: `TODO-PRED-THERMAL-MESH-GATE`
Date: `2026-07-13`

## Context Read

I read the current board and ownership context, the AGENT-291 terminal state,
the medium repaired reconstructed-`T` package, the fine repaired reconstructed-`T`
package, and the prior AGENT-284 Salt2 Closure-QOI mesh/GCI package.

Source paths:

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_AGENT-291.md`
- `.agent/journal/2026-07-13/salt2-fine-reconstructed-t-repair-plan-sbatch.md`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/outputs/medium/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/summary.json`

## Observed

AGENT-291 job `3293768` reached terminal Slurm state:

```text
3293768      s2_fine_T+  COMPLETED      0:0   00:22:33        c318-016
3293768.bat+      batch  COMPLETED      0:0   00:22:33        c318-016
3293768.0    python3.11  COMPLETED      0:0   00:22:32        c318-016
```

The fine repair summary says the repair smoke passed: clean reconstructed `T`,
successful temperature section sampling, and segment thermal extraction. It
also preserves the closure boundary: admission still requires review gates.

## Implemented

I added a reusable thermal mesh-gate builder:

- `tools/analyze/build_thermal_mesh_gate.py`
- `tools/analyze/test_thermal_mesh_gate.py`

The builder consumes medium and fine segment thermal CSVs and writes:

- `thermal_mesh_gate_qois.csv`
- `thermal_mesh_gate_blockers.csv`
- `thermal_mesh_gate_evidence.csv`
- `summary.json`
- `README.md`

It classifies each segment/quantity without running OpenFOAM and without
changing native solver outputs.

## Results

Package:

- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/`

Summary:

- QOI rows: `7`
- Medium/fine two-level complete rows: `5`
- Fit-admissible rows: `0`
- Publication-ready thermal GCI rows: `0`
- Admission decisions: `blocked_sign_review=5`,
  `blocked_missing_two_level_value=1`, `blocked_downcomer_policy=1`

The old blocker, missing fine reconstructed-`T` thermal extraction, is now
retired for Salt2. The active blockers are:

- sign convention/heat-balance review for the complete lower-leg and upcomer
  h/UA/Nu rows;
- missing coarse thermal triplets, so no GCI can be computed;
- lower-leg Nu is missing/nonfinite and direct Nu is not admitted;
- downcomer/right-leg thermal extraction remains policy-blocked.

## Interpretation

The medium/fine agreement is useful diagnostic evidence only. It is not
closure-admissible. Five rows have finite medium/fine values, but every finite
row still has `sign_consistent_heated_wall=False`, and the package has no
coarse/medium/fine thermal triplet for GCI.

Therefore thermal UA/HTC/Nu is partially unlocked operationally, in the sense
that the fine reconstructed-`T` corruption no longer blocks extraction. It is
not unlocked scientifically for closure fitting or thesis-grade GCI claims.

## Validation

- `python3.11 -m unittest tools.analyze.test_thermal_mesh_gate`
- `python3.11 -m py_compile tools/analyze/build_thermal_mesh_gate.py tools/analyze/test_thermal_mesh_gate.py`
- `python3.11 -m json.tool work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json`
- `wc -l work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_qois.csv work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_blockers.csv`

## Next Phase

Create a focused `thermal_admission_sign_heat_balance_review` task. Minimum
acceptance criteria:

1. Define heated-wall sign convention from wallHeatFlux, fluid enthalpy change,
   and segment orientation.
2. Recompute or audit lower-leg and upcomer heat duties against the sign
   convention.
3. Explain why lower-leg Nu is missing/nonfinite despite finite h and UA_prime,
   or mark Nu unavailable with a reproducible criterion.
4. Decide whether downcomer/right-leg remains excluded or needs a separate
   extraction policy.
5. Locate or generate coarse thermal triplets before any GCI or closure-fit
   admission claim.
