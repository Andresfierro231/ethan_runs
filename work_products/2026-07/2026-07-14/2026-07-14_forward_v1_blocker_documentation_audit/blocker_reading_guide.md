---
provenance:
  - blocker_documentation_matrix.csv
tags: [forward-model, blockers, reading-guide]
related:
  - README.md
task: AGENT-371
date: 2026-07-14
role: Forward-pred/Scientific-closure/Writer
type: reading_guide
status: complete
---
# Forward-v1 Blocker Reading Guide

Use this guide to answer why each AGENT-366 final forward-v1 gate remains blocked.

## fluid_reset_development_api

Why blocked: The Fluid API now accepts reset/development K, but API support is not pressure evidence and H1 is not launchable without admitted reset/development pressure rows.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/README.md`

Proof numbers: `api_added=MinorLosses.reset_development_k_by_segment; h1_launchable_after_this_slice=false`

Next unblock artifact: `reset_development_pressure_scorecard.csv`

## hydraulic_h1_pressure_evidence

Why blocked: Hydraulic tap lengths improved, but component/cluster K still has zero fit-admissible rows and H1 remains not launchable.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/README.md`

Proof numbers: `centerline_resolved_rows=12; centerline_blocked_rows=3; component_fit_admissible_rows=0; h1_faithful_launchable=false`

Next unblock artifact: `fit-admissible component/cluster K or f6_phi_re_hydraulic_scorecard.csv`

## pm5_matched_pressure_upcomer_metrics

Why blocked: The +/-5Q rows are terminal-harvested, but the matched pressure/upcomer extraction job has not reached terminal state and parsed metrics are absent.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/README.md`

Proof numbers: `job_id=3295901; sacct_state=PENDING; parsed_files_present=0`

Next unblock artifact: `pm5_corrected_q_matched_pressure_upcomer_metrics.csv`

## perturbation_split_policy

Why blocked: +/-5Q rows are sensitivity/admission evidence only today; they cannot expand independent train/validation/holdout rows without a dated split policy.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md`

Proof numbers: `pm5_harvest_rows=4; closure_fit_admissible_terminal_gate_rows=4; independent_training_expansion_rows=0`

Next unblock artifact: `perturbation_split_policy_update.csv`

## thermal_internal_nu

Why blocked: Thermal/internal-Nu fitting is rejected because current rows are diagnostic/validation-only or blocked by recirculation, mesh/GCI, sign, heat-balance, and matched-plane requirements.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/internal_nu_dependency_blockers.csv`

Proof numbers: `fitted_internal_nu_rows_consumable=false; upcomer use=diagnostic_validation_only; thermal fit rows=0`

Next unblock artifact: `thermal_internal_nu_admission_refresh.csv after matched-plane extraction and admission gates`

## boundary_hx_wall_radiation

Why blocked: Cooler/HX and wall boundary evidence is diagnostic or architecture-level; setup-only Fluid boundary/HX outputs are still required before final predictive HX can be claimed.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/README.md`

Proof numbers: `imposed cooler duty and realized wallHeatFlux remain runtime-disallowed; setup-only_boundary_hx_outputs.csv missing`

Next unblock artifact: `setup_only_boundary_hx_outputs.csv`

## sensor_map_policy

Why blocked: TP/TW sensor residuals are documented as post-solve validation targets, but a complete sensor score still needs explicit exclusion or coordinate policy for provisional/blocked labels.

Open first: `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/README.md`

Proof numbers: `sensor_error_rows=204; blocked/provisional labels remain target-only; TP/TW are not runtime inputs`

Next unblock artifact: `sensor_map_policy_refresh.csv`

