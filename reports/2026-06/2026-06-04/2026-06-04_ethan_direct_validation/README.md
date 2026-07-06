# Ethan Direct Validation Metrics

This report compares the 3D CFD rows directly against the Ethan-linked validation data and also carries raw channel errors plus a derived section heat-transfer breakdown.

## Metrics

- `exp_tp_rmse_k`: RMSE between CFD `TP1..TP6` and measured bulk temperature probes.
- `exp_tw_rmse_k`: RMSE between CFD wall-temperature stations and measured wall temperatures after averaging the 4 CFD azimuthal wall probes at each station, with `TW10` explicitly excluded from the RMSE calculation.
- `exp_all_temp_rmse_k`: RMSE across `TP1..TP6` plus wall stations excluding `TW10`; `TW10` is intentionally omitted from this combined RMSE.
- `tw10_excluded_from_rmse`: explicit boolean flag showing that `TW10` was excluded from the RMSE-based wall metrics.
- `tw10_raw_error_k`: raw signed `experiment - simulation` error for `TW10`, retained for transparency even though it is excluded from RMSE.
- `sim_mdot_kg_s`, `exp_mdot_kg_s`, and `exp_minus_sim_mdot_kg_s`: side-by-side CFD and experimental flow values with signed `experiment - simulation` error.
- `sim_total_wall_q_net_w`: signed net wall heat transfer from the saved `wallHeatFlux` patch totals; this is not a pure ambient-loss quantity.
- `sim_ambient_noncooling_proxy_w`: derived proxy for ambient losses outside the cooling branch, built from patchwise `wallHeatFlux` plus imposed positive-power patches.
- `sim_ambient_proxy_w`: derived proxy for total ambient-like loss, equal to `sim_ambient_noncooling_proxy_w` plus cooling-branch removal beyond the operating-point cooling duty.
- `sim_cooling_branch_total_removal_w`: total magnitude of removal through `pipeleg_upper_04_reducer`, `pipeleg_upper_05_cooler`, and `pipeleg_upper_06_reducer` from `wallHeatFlux.dat`.
- `exp_qhx_reference_w`: Ethan-linked HX-duty reference (`qhx_total_W`) from the validation-imposed campaign summary.
- `exp_q_external_loss_reference_w`: Ethan-linked ambient-loss reference (`qambient_total_W`) from the validation-imposed campaign summary.
- `exp_q_external_loss_abs_error_pct`: absolute percent error between `sim_ambient_proxy_w` and the Ethan-linked `qambient_total_W` reference.
- `sim_section_*_net_q_w`: signed section totals derived from `postProcessing/wallHeatFlux/1/wallHeatFlux.dat` using patch-name aggregation.
- final `exp_minus_sim_*` columns: signed channel-level errors (`experiment - simulation`) for all TP, TW, and mdot channels. `TW10` remains present here even though it is excluded from RMSE.

## Ethan-linked external-loss proxy

- The phrase `Ethan-linked external-loss proxy` refers to `qambient_total_W` from `validation_imposed_ethan_v2/imposed_hx_duty/<Case>/summary.csv`.
- That quantity is not a single raw column from the original validation table. It comes from the Ethan-prescribed segment-loss reconstruction used by the first-order validation-imposed campaign.
- It is still the most coherent current reference for total ambient loss, but it should be read as an Ethan-linked reconstructed target rather than a directly measured one-line ambient-loss measurement.

## Important note

- Temperature and mass-flow metrics are direct CFD-vs-measurement comparisons.
- The heat-loss comparison is now based on a derived 3D ambient-loss proxy from `wallHeatFlux.dat`, not on the older net `total_Q` value.
