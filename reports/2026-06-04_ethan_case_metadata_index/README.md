# Ethan Case Metadata Index

This is the June 4 expanded metadata index for the Ethan rows. It keeps the June 2 artifacts intact and adds clearer setup explanations, direct validation metrics, and explicit continuation provenance.

## Key interpretation rules

- `two_d_*` columns describe the 2D reference row published in the cross-model comparison contract.
- `one_d_stage*` columns describe first-order-model reference scenarios from that same contract.
- Those 2D/1D columns are enrichment metadata only. They are not direct evidence that the native 3D case used the same insulation or radiation settings.
- `cp_coeff_count` and `rho_coeff_count` are coefficient-array lengths from `case_config.yaml`, not counts of physical modes or components.
- `final_total_wall_heat_abs_w` is the magnitude of the final `total_Q.dat` sample from the 3D run and is used here as the CFD external-loss quantity.
- `val_salt_test_2_coarse_mesh_laminar` is a deliberate continuation-aware exception to the base-case fallback contract note: keep its `comparison_candidate` label conservative because the live package mixes heat `8602 s`, probe `1724 s`, and processor/runtime `3871 s` horizons rather than one synchronized terminal endpoint.

## Inputs

- Comparison contract CSV: `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-02_ethan_modern_runs_first_batch_v1/data/cross_model_case_contract.csv`
- Validation cases CSV: `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/validation_imposed_ethan_v2/config_used/validation_cases.csv`
- Validation summary root: `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/validation_imposed_ethan_v2/imposed_hx_duty`
- Wall probe map CSV: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/tp_tw_probe_locations.csv`

## Column glossary

- `source_id`: registered local source identifier for the imported or staged 3D CFD case.
- `case_id`: case identifier from case_config; includes variant suffixes like `_jin` or `_kirst` when present.
- `base_case_id`: base test family identifier with Jin/Kirst suffix removed; for example `salt_test_2`.
- `variant_label`: property-model branch label extracted from the case ID; blank means no Jin/Kirst split.
- `source_owner`: provenance owner from the local registry.
- `source_root`: absolute path to the native staged source tree; native solver outputs were not mutated.
- `active_runtime_root`: runtime tree actually inspected for current postProcessing, logs, and processor writes; differs from source_root for the active salt2 continuation.
- `fluid`: working-fluid label from case_config.
- `turbulence_model`: OpenFOAM flow model label from case_config.
- `heater_power_W`: imposed heater power in watts from the operating point.
- `cooling_power_W`: target HX/cooler duty in watts from the operating point.
- `T_init_K`: initial fluid temperature in kelvin.
- `nprocs`: MPI rank count configured for the original case.
- `scale_to_meters`: geometry scaling factor from model units to meters.
- `mesh_group_id`: mesh fingerprint/group identifier used to tie related cases together.
- `ncc_couples`: count of non-conformal coupling interfaces in the case.
- `geometry_dir`: geometry directory relative to the workspace when possible.
- `geometry_stl_count`: number of STL geometry files present under `constant/geometry`.
- `geometry_stl_examples`: up to 8 example STL filenames.
- `heater_h_W_m2K`: nominal heater-side external transfer coefficient in case_config bc_params.
- `heater_Ta_K`: heater-side ambient reference temperature in kelvin from case_config bc_params.
- `heater_emissivity`: heater emissivity value carried in case_config bc_params.
- `cooler_h_W_m2K`: nominal cooler-side external transfer coefficient in case_config bc_params.
- `cooler_Ta_K`: cooler-side ambient reference temperature in kelvin from case_config bc_params.
- `test_section_h_W_m2K`: nominal test-section external transfer coefficient in case_config bc_params.
- `test_section_Ta_K`: test-section ambient reference temperature in kelvin from case_config bc_params.
- `insulated_h_W_m2K`: nominal insulated-region external transfer coefficient in case_config bc_params.
- `insulated_Ta_K`: insulated-region ambient reference temperature in kelvin from case_config bc_params.
- `three_d_outer_insulation_thickness_m`: outer insulation-layer thickness parsed from the first layered `rcExternalTemperature` entry in `0/T`.
- `three_d_outer_insulation_thickness_in`: same parsed outer insulation thickness converted to inches; this fills the missing salt2 native-case insulation context.
- `three_d_loss_bc_summary`: plain-language summary of how the 3D case treats wall losses in `0/T`.
- `three_d_radiation_summary`: plain-language summary of how radiation-like exchange appears in the 3D wall boundary condition file.
- `mesh_kernel_factor`: mesh-generation kernel factor from case_config.
- `mesh_kernel_blend`: mesh-generation kernel blend from case_config.
- `mesh_core_ratio`: mesh core-ratio control from case_config.
- `inflation_first_cell_size`: first wall-adjacent inflation cell size from case_config.
- `inflation_bulk_cell_size`: bulk inflation cell size from case_config.
- `inflation_c2c_expansion`: cell-to-cell inflation expansion ratio from case_config.
- `convergence_enabled`: whether the coded convergence monitor was enabled.
- `convergence_check_interval`: iteration interval between convergence checks.
- `convergence_min_iterations`: minimum iteration count before convergence checks activate.
- `convergence_qoi_rtol`: relative tolerance used by the coded convergence monitor.
- `convergence_qoi_window`: window length used by the coded convergence monitor.
- `mu_spec_type`: viscosity model family name from case_config; `expInvT` means `A*exp(b0/T+b1/T^2+...)`.
- `mu_coeff_count`: number of viscosity coefficients in the chosen model.
- `mu_coeff_summary`: human-readable viscosity-model summary; this distinguishes the Jin and Kirst coefficient sets even though both use `expInvT`.
- `kappa_spec_type`: thermal-conductivity model family name from case_config.
- `kappa_coeff_count`: number of thermal-conductivity coefficients.
- `kappa_coeff_summary`: human-readable conductivity-model summary.
- `cp_coeff_count`: length of the `Cp_coeffs` array in case_config; it is a coefficient-array length, not a count of physical Cp components.
- `cp_model_summary`: human-readable Cp model summary; for the salt cases this shows the array is effectively constant Cp with only the c0 term active.
- `rho_coeff_count`: length of the `rho_coeffs` array in case_config; again this is a coefficient-array length, not a physical component count.
- `rho_model_summary`: human-readable density-model summary.
- `walltime`: requested walltime string in case_config.
- `run_status`: best current runtime state; uses live scheduler state for the active salt2 continuation when available.
- `run_termination_reason`: reason parsed from the solver log or set from live continuation context.
- `final_time`: latest physical time observed across the extracted postProcessing files.
- `latest_processor_time`: latest numeric processor-write directory seen under `processors*`.
- `qoi_vs_processor_time_gap_s`: latest processor time minus latest extracted postProcessing time; positive values signal that the QoI products lag behind newer writes.
- `convergence_reached`: whether the coded convergence monitor explicitly reported convergence in the parsed solver log.
- `convergence_iteration`: iteration where the coded convergence monitor declared convergence.
- `convergence_dTsigma`: temperature-spread convergence metric from the coded convergence monitor.
- `convergence_tol`: coded convergence tolerance from the solver log summary.
- `convergence_status_provenance`: explains whether convergence status came purely from the old solver log or from that log plus an active continuation context.
- `continuation_job_id`: active continuation job ID when this row is being tracked as a live continuation.
- `continuation_scheduler_state`: live scheduler state from `squeue` for the active continuation job when available.
- `mdot_mean_abs_kg_s`: mean absolute mass flow from the four monitored faceZones at the latest extracted time.
- `final_total_wall_heat_abs_w`: absolute value of the final `postProcessing/total_Q.dat` sample; this is the magnitude of the net all-wall heat-transfer sum, not a pure ambient-loss quantity.
- `sim_total_wall_q_net_w`: signed total wall heat transfer reconstructed from the latest `wallHeatFlux.dat` patch totals.
- `sim_ambient_proxy_w`: derived ambient-loss proxy from `wallHeatFlux.dat`, built from passive losses plus powered-section deficits and cooling-branch excess beyond the operating-point cooling duty.
- `probe_T_avg_K`: average of the latest `TP1..TP6` CFD probe temperatures in kelvin.
- `two_d_ins_s1_thickness_in`: 2D comparison-contract insulation thickness for section 1 in inches; this is a 2D reference-scenario field, not a native 3D input.
- `two_d_ins_s2_thickness_in`: 2D comparison-contract insulation thickness for section 2 in inches; again a 2D reference-scenario field.
- `two_d_radiation_on`: 2D comparison-contract radiation flag; this does not by itself prove the 3D case had radiation on or off.
- `one_d_stage1_scenario`: name of the first-order-model stage-1 scenario from the cross-model comparison contract.
- `one_d_stage1_insulation_thickness_in`: stage-1 first-order-model insulation thickness in inches from the comparison contract.
- `one_d_stage1_radiation_on`: stage-1 first-order-model radiation flag from the comparison contract.
- `one_d_stage2_source_available`: whether the comparison contract published a stage-2 first-order-model source row.
- `one_d_stage2_scenario`: name of the first-order-model stage-2 scenario from the comparison contract.
- `comparison_contract_match_type`: how this metadata row was enriched from the comparison contract: exact source match, base-case fallback, or unmatched.
- `comparison_ready`: comparison-disposition label from the published comparison contract.
- `disposition_note`: published comparison-contract note about whether the row was considered ready for validation comparison.
- `exp_case_name`: linked experimental validation case name used by the direct CFD-vs-experiment report.
- `exp_reference_status`: whether a direct validation row was found for this case.
- `exp_tp_rmse_k`: direct CFD-vs-experiment RMSE for the bulk-fluid temperature probes TP1..TP6.
- `exp_tw_rmse_k`: direct CFD-vs-experiment RMSE for wall-temperature stations after averaging the 4 CFD wall subprobes per station, with TW10 explicitly excluded.
- `exp_all_temp_rmse_k`: direct CFD-vs-experiment RMSE across TP1..TP6 plus wall stations excluding TW10.
- `exp_mdot_abs_error_pct`: direct absolute percent mass-flow error against the experimental measured mass flow rate.
- `exp_q_external_loss_reference_w`: Ethan-linked external-loss proxy used for comparison; drawn from `validation_imposed_ethan_v2` `qambient_total_W`.
- `exp_q_external_loss_reference_status`: documents that the external-loss reference is an Ethan-prescribed-segment-loss proxy rather than a single direct measured column in the validation table.
- `exp_q_external_loss_abs_error_pct`: absolute percent error between CFD wall heat loss and the Ethan-linked external-loss proxy.
- `loss_setup_summary`: plain-language note on how heat-transfer coefficients are treated in the 3D setup.
- `friction_treatment_summary`: plain-language note on how friction is treated in the 3D CFD and how blank reduced friction columns should be interpreted.
- `base_case_family_note`: case-family note used to explain special relationships such as `val_salt_test_2` versus the viscosity-screening salt2 rows.
- `assumption_note`: full setup note combining wall-loss treatment, radiation treatment, property models, and friction interpretation.
