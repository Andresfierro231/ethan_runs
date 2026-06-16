# All-Salt Behavior Package

This package extends the Salt 2 behavior work to the full salt campaign and separates coded convergence from practical usability.

## Main findings

- Salt Test 2, 3, and most of Salt Test 4 are practically usable now for steady-state analysis, even where the coded convergence monitor never fired.
- Salt Test 1 remains the main exception: both current rows are flat in the tail, but they sit on a materially larger net heat-balance residual floor and should not be treated as clean steady-state representatives.
- Jin versus Kirst changes mass-flow agreement more strongly than it changes the derived ambient-loss proxy. That is evidence that the remaining ambient-loss error is dominated by a shared wall-loss model bias rather than by the viscosity branch alone.
- Salt 2 is the strongest current validation case. The native val_salt_test_2 continuation remains the primary manuscript representative for Salt 2.
- Salt 4 Jin has now been staged and resubmitted for a capped 72-hour continuation to improve the steady-state sensitivity evidence for the user-chosen representative branch.

## Representative-case policy

- `salt_test_1`: steady representative `none yet`, manuscript representative `none yet`, continuation candidate `viscosity_screening_salt_test_1_jin_coarse_mesh`. No current Salt 1 row is clean enough for a steady-state representative; Jin is the preferred continuation candidate because it avoids the false-convergence interpretation and has slightly better mass-flow error than Kirst.
- `salt_test_2`: steady representative `val_salt_test_2_coarse_mesh_laminar`, manuscript representative `val_salt_test_2_coarse_mesh_laminar`, continuation candidate `val_salt_test_2_coarse_mesh_laminar`. Use the native val_salt_test_2 continuation as the primary representative; retain staged Jin and Kirst as sensitivity comparisons for viscosity and setup changes.
- `salt_test_3`: steady representative `viscosity_screening_salt_test_3_kirst_coarse_mesh`, manuscript representative `viscosity_screening_salt_test_3_jin_coarse_mesh`, continuation candidate `none`. Salt 3 Jin is the current preferred representative because it remains practically steady and has the better mass-flow agreement.
- `salt_test_4`: steady representative `viscosity_screening_salt_test_4_kirst_coarse_mesh`, manuscript representative `viscosity_screening_salt_test_4_jin_coarse_mesh`, continuation candidate `viscosity_screening_salt_test_4_jin_coarse_mesh`. Salt 4 Kirst is the steadier current reference, but Salt 4 Jin is the chosen manuscript sensitivity representative and has been extended in the background to improve its steady-state credibility.

## Ambient-loss interpretation

- The current 3D ambient-loss mismatch is systematic but not catastrophic. Most use-ready salt rows underpredict the Ethan-linked ambient-loss proxy by roughly 17--21\%.
- The Salt 2 triad is especially informative: the val row, staged Jin row, and staged Kirst row all land near the same derived ambient-loss magnitude despite differing in insulation thickness, cooler h, runtime, and viscosity branch. That strongly suggests a shared external wall-loss modeling bias.
- The shared bias could come from one or more of the following: external film coefficient calibration, external ambient or surrounding-surface temperature assumptions, emissivity/radiation treatment details, or parasitic conduction paths not represented in the current wall-loss boundary partition.

## Source files

- `all_salt_case_status.csv`: cross-case state, usability, and validation summary.
- `all_salt_steady_window_summary.csv`: last-window statistics and drift metrics for mdot, TP mean, total Q, and section heat terms.
- `ambient_loss_audit.csv`: case-by-case ambient-loss accounting and hypothesis notes.
- `jin_vs_kirst_summary.csv`: direct paired comparisons for tests with both viscosity branches.
- `representative_case_selection.csv`: explicit selection rationale for manuscript-facing representative rows.
