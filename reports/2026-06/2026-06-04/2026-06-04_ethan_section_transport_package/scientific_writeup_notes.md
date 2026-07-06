# Scientific Write-up Notes

## Observed outputs

- Latest-time section pressure drops are now available for all processed salt rows using non-destructive OpenFOAM postprocessing on reconstructed `p` and `p_rgh` fields.
- Section heat-transfer drift statistics are now available from the existing `wallHeatFlux.dat` time histories for every processed salt row.
- The representative summary table joins these section-transport quantities to the previously generated validation metrics and usability classifications.

## Interpretation

- The section-pressure products are the first direct 3D basis for discussing loop resistance by branch instead of only using global mdot mismatch.
- Across the usable Salt 2-4 rows, the upper leg is consistently the dominant `|Δp_rgh|` branch, with the left and right legs forming the next tier of hydraulic loss.
- Jin-versus-Kirst differences are now visible hydraulically: for Salt 2-4, Jin usually reduces upper-leg and left-leg `|Δp_rgh|` relative to Kirst, which is directionally consistent with its better mdot agreement.
- The section-heat drift products make it possible to separate cases that are globally flat from cases that still show a meaningful late-time drift in a specific branch or loss channel.
- The largest late-window heat drifts are usually in the junction-region wall heat and the derived ambient-loss proxy, not in the main heater or cooling-branch totals.
- Because the reconstructed `T` field is not yet clean enough for generic surface sampling, the current package should be used for branch-scale resistance and heat accounting, not yet for definitive axial `h(x)` or `Nu(x)` claims.

## Representative rows

- `val_salt_test_2_coarse_mesh_laminar` for `salt_test_2`: TP RMSE `2.573896609361759` K, TW RMSE excluding TW10 `6.2626823688395215` K, mdot error `18.951017976190467` %, external-loss error `20.593912894777922` %.
- `viscosity_screening_salt_test_3_jin_coarse_mesh` for `salt_test_3`: TP RMSE `2.1338924649904922` K, TW RMSE excluding TW10 `6.904353795656094` K, mdot error `14.711376500000014` %, external-loss error `19.009679138345895` %.
- `viscosity_screening_salt_test_4_jin_coarse_mesh` for `salt_test_4`: TP RMSE `1.687564177784045` K, TW RMSE excluding TW10 `7.555170550541495` K, mdot error `15.496810024875622` %, external-loss error `17.40163440703854` %.

## Next analytical step

- Add a compute-node postprocessing path for clean transient `p_rgh` histories and axial surface sampling so the manuscript can move from branch-wise section metrics to true distance-resolved transport coefficients.
