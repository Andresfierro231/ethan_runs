# Ethan 1D Model Discrepancy Report

This report compares the salt-property and scenario assumptions encoded in
Ethan's shared CFD run trees against the current 1D model branches in the
sibling `cfd-modeling-tools/tamu_first_order_model/Fluid` workspace.

## Scope

- Shared-run evidence inspected here comes from staged CFD case configs under:
  - `staging/modern_runs/2026-06-01_full_extractable_batch/salt/.../case_config.yaml`
- Current 1D model evidence inspected here comes from:
  - `tamu_first_order_model/Fluid/tamu_loop_model_v2/materials.py`
  - `tamu_first_order_model/Fluid/results/diagnostics/predictive_validation_salt_current_contract_array_v1/...`
  - `tamu_first_order_model/Fluid/results/diagnostics/salt_promoted_property_matrix_v1/...`
  - `tamu_first_order_model/Fluid/results/diagnostics/validation_imposed_ethan_v2/...`
- This report does **not** yet claim that Ethan's shared run trees contain a
  fully archived 1D code copy. In the current accessible evidence, the strong
  source of discrepancy is the run-side 3D property/config metadata plus the
  current 1D workspace outputs.

## Main discrepancies

### 1. The current 1D default does not match Ethan's converged Kirst runs

- Current 1D default:
  - property set name: `salt_current`
  - model: fully tabulated interpolation from `SALT_ROWS`
- Converged shared 3D Kirst runs:
  - constant `Cp = 1423.47 J/kg-K`
  - `rho(T) = 2293.6 - 0.7497*T`
  - `k(T) = 0.78 - 1.25e-3*T + 1.6e-6*T^2`
  - viscosity branch: `expInvT` with coefficients `[6.757e-05, 2247.11]`

That is a material formulation mismatch, not just a naming difference.

### 2. The existing promoted 1D salt branch is closer to Ethan's Jin runs, not Kirst

- Current 1D promoted branch:
  - property set name: `salt_promoted`
  - constant `Cp` from the mean of `SALT_ROWS`
  - density and conductivity still tabulated from `SALT_ROWS`
  - viscosity is a Jin-style exponential fit over the tracked table
- Shared 3D Jin runs:
  - constant `Cp = 1423.47 J/kg-K`
  - linear `rho(T)`
  - polynomial `k(T)`
  - viscosity `expInvT` coefficients `[0.001149, -810.896, 780600]`

So even when the promoted branch moves toward Ethan's Jin assumptions, it still
does not reproduce the shared 3D data structure exactly because the 1D promoted
branch keeps density and conductivity tabulated instead of using the explicit
run-side forms.

### 3. The converged visualization candidates are both Kirst, but the current 1D comparison machinery is not Kirst-aware

- Current converged CFD comparison candidates:
  - `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`
- Current 1D workspace branches available in evidence here:
  - `salt_current`
  - `salt_promoted`

There is no explicit `salt_kirst` 1D branch in the inspected current 1D
workspace evidence.

### 4. Scenario mismatches are mixed in with property mismatches

- The converged CFD comparison-candidate rows map to stage-1 scenario
  `predictive_airside_ins_1.0in_rad_1`.
- The separately inspected 1D validation run `validation_imposed_ethan_v2`
  instead uses `imposed_hx_duty`, which prescribes ambient losses from Ethan's
  measured-state wall-loss model.

That means some current 1D-vs-CFD disagreements may come from scenario choice,
not only from material properties.

## Evidence table

See:

- [property_model_comparison.csv](property_model_comparison.csv)
- [scenario_behavior_comparison.csv](scenario_behavior_comparison.csv)

## Practical determination

- We should not describe the current 1D default as matching Ethan's converged
  Kirst CFD runs.
- We should not describe the current 1D promoted branch as universally matching
  Ethan's salt runs either; it is at best Jin-adjacent and still structurally
  different.
- The next defensible path is a variant-aware 1D contract:
  - `salt_current`
  - `salt_promoted_jin`
  - `salt_kirst`

## Recommended next actions

- The explicit `salt_kirst` branch is now added in the sibling 1D workspace.
- Re-run the stage-1 predictive scenario for Salt 1 and Salt 2 under that
  Kirst-style branch before making 1D-vs-3D claims from the converged Kirst CFD
  rows.
- Keep `validation_imposed_ethan_v2` labeled as a measured-loss scenario, not a
  like-for-like predictive counterpart to the current converged CFD rows.

## Secure shared OpenFOAM tree check

A direct search of `/scratch/secure/nuclear/OpenFOAM_V13/` found the shared
OpenFOAM 13 runtime and bootstrap script, but did not reveal a separate archived
TAMU loop 1D model. The useful result from that path is therefore runtime
comparison, not additional 1D source provenance.
