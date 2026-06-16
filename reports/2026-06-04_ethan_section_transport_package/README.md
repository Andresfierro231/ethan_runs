# Ethan Section Transport Package

This package adds a reusable section-transport layer on top of the June 4 Ethan reporting stack.

## Scope

- Extract latest-time section pressure information from non-destructively reconstructed `p` and `p_rgh` fields.
- Reuse the existing `wallHeatFlux.dat` reductions to rank section-wise heat-transfer drift over the last analysis window.
- Provide manuscript-facing summary rows for the current representative salt cases.

## Important limitations

- Pressure extraction is latest-time only in this first pass. It is meant to support section ranking and loop-resistance interpretation, not a full transient hydraulic history yet.
- Pressure-drop signs follow the geometric `start -> end` patch ordering from the mesh naming. Use the absolute pressure-drop columns for loss ranking.
- The current axial `h(x)` / `Nu(x)` analysis is not included here because the reconstructed root-level `T` field is not reliable enough for generic surface sampling in this workflow. The section heat and pressure products remain valid because they use `wallHeatFlux.dat`, existing probe outputs, and patch-averaged pressure fields only.
- `TW10` remains excluded from manuscript RMSE scorecards elsewhere. This package does not change that rule.

## Cases processed

- `val_salt_test_2_coarse_mesh_laminar`: `run_status=running`, `essential_steadiness_class=essentially_steady`
- `viscosity_screening_salt_test_1_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=not_steady_enough`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`: `run_status=completed`, `essential_steadiness_class=not_steady_enough`
- `viscosity_screening_salt_test_2_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`: `run_status=completed`, `essential_steadiness_class=essentially_steady`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=borderline_but_usable`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`

## Pressure sections

The major section pressure drops are extracted between these non-conformal interface patches:

- `lower_leg`: `ncc_pipeleg_lower_01_fitting_start` -> `ncc_pipeleg_lower_09_fitting_end`
- `right_leg`: `ncc_pipeleg_right_01_lower_start` -> `ncc_pipeleg_right_03_upper_end`
- `upper_leg`: `ncc_pipeleg_upper_01_straight_start` -> `ncc_pipeleg_upper_09_straight_end`
- `left_leg`: `ncc_pipeleg_left_01_upper_start` -> `ncc_pipeleg_left_07_lower_end`
- `test_section_branch`: `ncc_pipeleg_left_03_fitting_start` -> `ncc_pipeleg_left_05_fitting_end`
- `connector_span`: `ncc_pipeleg_left_02_connector_end` -> `ncc_pipeleg_left_06_connector_start`

## Current scientific use

- The pressure-drop columns are suitable for first-pass loop-resistance comparisons across Jin, Kirst, and validation-style runs.
- The section-heat drift rows are suitable for checking whether the net heat-balance tail is still moving materially in any section, even when the solver convergence monitor did not declare convergence.
- The representative summary table is the manuscript-ready bridge product for the next write-up pass.

## Representative snapshot

- `val_salt_test_2_coarse_mesh_laminar`: ambient proxy `187.75655921057998` W, cooling branch `136.35074002` W, test-section branch `|Δp_rgh|=1.30412733` Pa
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: ambient proxy `211.76299764877` W, cooling branch `150.76963870000003` W, test-section branch `|Δp_rgh|=1.88050359` Pa
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: ambient proxy `244.24024581527993` W, cooling branch `169.22681362` W, test-section branch `|Δp_rgh|=2.900423739999999` Pa
