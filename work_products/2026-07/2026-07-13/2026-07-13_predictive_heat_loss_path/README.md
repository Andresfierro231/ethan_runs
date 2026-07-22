# Predictive heat-loss path package

Task: `AGENT-270`

This package converts the current thermal evidence stack into a practical path
toward predictive heat loss. It is a synthesis package only: it does not edit
Fluid, launch OpenFOAM, mutate native solver outputs, or admit blocked thermal
rows into closure fits.

## Outputs

- `control_volume_effective_thermal_table.csv`: segment/control-volume table
  with CFD realized wall heat, imposed heat, external `hA`, physical-interface
  enthalpy residuals, and available effective internal `h`, `Nu`, and `UA'`.
- `cooler_hx_duty_comparison.csv`: separates the current 1D cooler/HX duty
  error from internal Nu and ambient-wall residual lanes.
- `one_d_replay_mode_scores.csv`: normalized fixed-mdot replay modes.
- `fit_parameter_summary.csv`: low-dimensional correction candidates and their
  current fit status.
- `heldout_validation_scores.csv`: held-out Salt2/3/4 readiness scaffold only;
  no fitted parameters are claimed.
- `uncertainty_readiness.csv`: time-window, mesh, radiation, interface, and
  corrected-Q readiness gates.
- `summary.json`: machine-readable package summary.

## Main findings

1. The cooler/HX boundary remains first-order. The fixed-mdot baseline mean
   absolute Tmean error is 63.746 K,
   while replacing only the predictive cooler duty with CFD cooler duty reduces
   it to 4.456 K.
2. Current control-volume rows are useful diagnostics, but they are not
   thesis-strength thermal fit rows. The synthesis has
   0 fit-candidate rows after mesh,
   interface, and thermal-admission gates.
3. Radiation must stay inseparable from `rcExternalTemperature` wall heat flux
   until a separate solver output term or controlled rerun exists.
4. Internal Nu is treated as a postprocessed CFD effective quantity
   (`h_eff = q_wall / (T_wall - T_bulk)`, `Nu_eff = h_eff D_h/k_bulk`), while
   the 1D model remains a predictive resistance network. This package keeps
   those roles separate.

## Recommended next sequence

1. Fit the external cooler/HX parameterization first using held-out Salt cases.
2. Only after that residual is reduced, test one global internal Nu multiplier
   before segment/profile descriptors.
3. Add ambient external h/radiation terms only with an inseparable or
   explicitly audited radiation contract.
4. Promote corrected-Q/low-heat rows only after row-specific terminal,
   latest-time, and uncertainty admission checks.
5. Attach time-window and mesh uncertainty before making predictive claims.

## Source packages

- `thermal_boundary_patch_role_table`: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table`
- `patchwise_heat_ledger_enthalpy_interfaces`: `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces`
- `thermal_mismatch_remedy_deep_dive`: `work_products/2026-07/2026-07-08/2026-07-08_thermal_mismatch_remedy_deep_dive`
- `thermal_openfoam_interface_sampling`: `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling`
- `legacy_segment_htc_uaprime`: `work_products/2026-07/2026-07-01/2026-07-01_claude_thermal_downcomer`
