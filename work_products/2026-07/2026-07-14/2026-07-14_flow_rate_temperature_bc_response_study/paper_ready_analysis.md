# Paper-Ready Flow-Rate, Temperature, and Boundary-Condition Analysis

Task: `AGENT-359` additive hardening of `AGENT-351`
Date: `2026-07-14`

## Scope And Data

This analysis joins case-level boundary-condition metadata, time-series
mdot/temperature aggregates, patch-role OpenFOAM boundary reductions, submitted
steady-state labels, false-steady perturbation provenance, and split-aware
corrected +/-5Q terminal-harvest evidence. It does not run OpenFOAM, mutate
native CFD solver outputs, modify registry/admission state, or edit external
`../cfd-modeling-tools`.

The study is suitable for paper methods/results text as an audited observational
dataset. It is not a controlled causal fit of flow rate against temperature
because the Salt2/Salt3/Salt4 design changes temperature, heater power, cooler
power, and boundary coefficients together.

## Admitted Mainline Rows

- `salt2_jin`: |mdot|=0.013199343 kg/s, probe T=448.425276 K, heater=265.7 W, cooler=56.34 W, split/use=`training`.
- `salt3_jin`: |mdot|=0.014981961 kg/s, probe T=462.105529 K, heater=297.5 W, cooler=60.55 W, split/use=`validation`.
- `salt4_jin`: |mdot|=0.017080866 kg/s, probe T=477.976692 K, heater=337.6 W, cooler=65.98 W, split/use=`holdout`.

The admitted/usable mainline rows show a monotonic increase in |mdot| with
temperature: for time-series probe temperature, n=`3`,
Pearson r=`0.999991`, R2=`0.999982`, and
slope=`0.000131371925` kg/s/K. Heater power gives
n=`3`, r=`0.999809`, and slope=`0.000053914802`
kg/s/W; cooler setup power gives n=`3`, r=`0.999664`.
These values document the observed ordering, not an independent closure law.

## Boundary Conditions And Heat Roles

Case-level setup scalars document the intended initial temperature, heater
power, cooler setting, and external boundary coefficients. Patch-role reductions
document the realized OpenFOAM boundary roles and total `wallHeatFlux` by heater,
cooler, ambient wall, test section, and junction/other surfaces. Realized
`wallHeatFlux` is a diagnostic result and must not be used as a predictive
runtime input.

Radiation semantics are explicit: CFD `rcExternalTemperature` includes
emissivity and surroundings-temperature radiation in total `wallHeatFlux`, and
there is no separate exported `qr` term in the current CFD outputs. Paper text
should therefore describe radiation as embedded in the boundary heat flux, not
as a separately measured heat-loss channel.

## Perturbation Evidence

Old Q perturbation rows remain invalid false-steady provenance. Their observed
|mdot| movement is far smaller than the expected Q^(1/3)-type operating-point
movement, so they cannot support a flow-rate/temperature response conclusion.

The corrected +/-5Q rows are handled separately. This package includes
`4` terminal-harvested corrected-Q rows from the split-aware AGENT-353
tables and their heat-role reductions. They are sensitivity/admission evidence
only: they do not expand the training, validation, or holdout sets until the
perturbation split policy and required operating-point gates are explicitly
updated.

## Conclusions

- **C1_mainline_flow_temperature_ordering**: Across admitted Salt2/Salt3/Salt4 mainline rows, |mdot| rises from 0.013199343 to 0.017080866 kg/s as time-series probe temperature rises from 448.425 to 477.977 K. Claim strength: observational monotonic trend; limited by n=3 and covarying boundary conditions. Limitation: not a controlled flow-temperature law; Salt2 and Salt3 remain heat-drifting in steady labels.
- **C2_power_temperature_boundary_confounding**: Initial temperature, probe temperature, heater power, cooler power, and external-h settings co-vary with the Salt case design. Claim strength: valid as design documentation and context. Limitation: do not interpret scalar correlations as independent causal coefficients.
- **C3_boundary_heat_roles_scale_with_case**: Patch-role reductions show heater input, cooler removal, and passive heat losses increasing in magnitude from Salt2 to Salt4. Claim strength: usable for boundary-condition audit and qualitative heat-path explanation. Limitation: realized wallHeatFlux is a diagnostic outcome, not a predictive runtime input.
- **C4_old_q_perturbations_are_not_physical_response_rows**: Old Q perturbation rows are false-steady: observed mdot moves are 0.004-0.283%, well below expected 1.64-3.45% movement. Claim strength: strong exclusion/admission claim. Limitation: none for exclusion; these rows remain provenance only.
- **C5_corrected_pm5q_rows_are_sensitivity_evidence**: 4 corrected +/-5Q rows are terminal-harvested and split-pending, with heat-role reductions now linked into this study. Claim strength: usable as sensitivity/admission evidence, not independent fit rows. Limitation: requires perturbation split policy, BC-role refresh, and operating-point/matched-plane gates before independent training or scoring use.
- **C6_radiation_semantics**: For current CFD rows, rcExternalTemperature includes radiation in total wallHeatFlux; no separate exported qr term exists. Claim strength: required methods statement. Limitation: do not double-count radiation or present a separate CFD qr heat-loss budget.
