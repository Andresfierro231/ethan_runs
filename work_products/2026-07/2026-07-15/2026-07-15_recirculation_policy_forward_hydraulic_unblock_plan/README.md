# Recirculation Policy + Forward-v1 / Hydraulic Residual Unblock Plan

Date: 2026-07-15
Task: AGENT-419

## Bottom Line

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.
The current AGENT-406 PM5 rows and AGENT-409 raw two-tap rows do not unlock
true single-stream `Nu`, `f_D`, or `K`. They are useful, but only as
section-effective diagnostics because reverse area/mass fractions are material
and the pressure rows are reduced-pressure, report-both-signs proxies without a
final component-loss admission gate.

## Outputs

- `recirculation_policy_decision_table.csv` (18 rows)
- `coefficient_label_admission_policy.csv` (7 rows)
- `current_evidence_recirculation_classification.csv` (15 rows)
- `final_forward_v1_unblock_chain.csv` (8 rows)
- `final_hydraulic_residual_unblock_chain.csv` (7 rows)
- `source_manifest.csv`
- `summary.json`

## Admission Rules

Reverse-flow fractions are now admission rules, not caveats:

- `RAF = A(U_axial < 0) / A_total`.
- `RMF = |sum(rho U_axial dA for U_axial < 0)| / sum(|rho U_axial| dA)`.
- `SVF = area-mean ||U_secondary|| / area-mean ||U||`.
- `Ri = Gr / Re^2`, using the same property lane and extraction window as the
  row being admitted.
- `h_proxy = q_wall'' / (T_wall - T_bulk)`.

Default fit admission for true single-stream `Nu`, `f_D`, or component `K`
requires `RAF < 0.01` and `RMF < 0.01`, plus the appropriate sign, pressure,
boundary, mesh/GCI, and source-path gates. Rows with `RAF >= 0.20` or
`RMF >= 0.20` are material recirculation rows and must be labeled
section-effective or diagnostic-only. Rows in the transition band
`0.05 <= RAF/RMF < 0.20` cannot fit true single-stream coefficients.

Thermal residuals must not be hidden in internal Nu. Heater fraction, cooler/HX
removal, passive wall/external convection, storage, branch mixing, and radiation
metadata remain separate residual owners. CFD `wallHeatFlux` from
`rcExternalTemperature` already includes radiative exchange; no separate `qr`
export is assumed here.

Hydraulic residual decomposition is:

`Delta_p_residual = Delta_p_observed - Delta_p_model`

with:

`Delta_p_model = Delta_p_straight + Delta_p_localized_K + Delta_p_reset_development_K + Delta_p_recirculation_onset + Delta_p_buoyancy_density_gradient + Delta_p_acceleration_if_applicable`

and:

`Delta_p_straight = f_D (L / D_h) q_ref`

`K_local = Delta_p_local / q_ref`

where `Delta_p_local` is only admissible after straight/distributed loss has
been subtracted and the taps have admitted pressure definition/orientation.

## Current Evidence Classification

AGENT-406 contributes 12 PM5 rows. All are diagnostic-only
under this policy. They have useful wall-band and matched-plane fields,
including `rho/Re/Pr/Ri/Gr/Ra`, but material reverse mass/area and sign/section
semantics prevent true single-stream `Nu`, `f_D`, or `K` fitting.

AGENT-409 contributes 3 raw two-tap rows. They are
diagnostic pressure evidence only: coarse, reduced `p_rgh` proxy rows with
report-both-signs orientation and material reverse-area proxies. The valid label
is `K_section_effective_recirculating_diagnostic` or apparent pressure-gradient
diagnostic, not true component `K`.

## Shortest Executable Path

1. Run the setup-only HX/cooler scorecard using the Fluid setup boundary hook:
   Salt2 fit, Salt3 validation, Salt4 holdout, with the fitted scalar frozen
   after training.
2. Produce a raw pressure admission package that converts or replaces the
   reduced `p_rgh` proxy with an admitted static pressure definition, fixes tap
   upstream/downstream orientation, subtracts straight loss, and carries mesh/GCI.
3. Refresh PM5/F6 pressure-onset review using this policy: current PM5 rows may
   support onset diagnostics, but they cannot train true `f_D` or `K`.
4. Keep internal-Nu closed to fitting until a row has wallHeatFlux, interpretable
   positive `h_proxy`, low RAF/RMF, accepted heat-balance residual, and mesh/GCI.
5. Freeze a final forward-v1 scorecard only after the thermal boundary model,
   hydraulic attribution, mesh/UQ, and sensor split all use the same
   validation/holdout discipline and coefficient-label policy.

## Guardrails

- Native CFD solver outputs were not mutated.
- External `../cfd-modeling-tools` was not edited.
- Staged/repaired/smoke outputs remain diagnostic until an explicit admission
  gate admits them.
- Current recirculating evidence does not unlock final forward-v1 or final
  hydraulic residual attribution.
