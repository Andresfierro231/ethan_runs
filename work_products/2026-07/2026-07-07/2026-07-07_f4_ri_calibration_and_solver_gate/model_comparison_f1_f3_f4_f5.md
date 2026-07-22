# Model Comparison: F1 / F3 / F4 Candidate / F5

Raw observations:

- The per-span comparison is against the de-buoyed CFD target `f_corrected/f_lam`.
- `F5_per_leg_CFD_multiplier` is the CFD per-leg multiplier and therefore matches the target by construction.
- Existing mdot diagnostics are copied from the July 1 per-leg/global 1D comparison and remain diagnostic-only.

Interpretation:

- F4 candidate quality should be judged first on pressure-resistance distribution, not loop mdot.
- Mdot remains entangled with the known 1D thermal-driver mismatch documented in the July 2/July 7 notes.

| case_id | model_form | pred_mdot_kg_s | cfd_mdot_kg_s | pct_error_vs_cfd_target | interpretation_caveat |
| --- | --- | --- | --- | --- | --- |
| salt_2 | default(mult=1) | 0.017105637669666017 | 0.01318354663 | 29.74989317928341 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_2 | global_mean_mult | 0.012576755543386345 | 0.01318354663 | -4.602639211157813 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_2 | per_leg_friction | 0.01189636257650172 | 0.01318354663 | -9.76356430954027 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_3 | default(mult=1) | 0.020108733381844303 | 0.01496689828 | 34.35471402057463 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_3 | global_mean_mult | 0.01447896435078946 | 0.01496689828 | -3.2600871608953 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_3 | per_leg_friction | 0.013500478452184314 | 0.01496689828 | -9.7977536853794 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_4 | default(mult=1) | 0.023756879589009468 | 0.01698467657 | 39.87242848634043 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_4 | global_mean_mult | 0.016454440015466795 | 0.01698467657 | -3.1218525259984036 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
| salt_4 | per_leg_friction | 0.015241892318128513 | 0.01698467657 | -10.260921040732459 | mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect |
