# Upcomer Recirculation And Internal-Nu Admissibility

Date: 2026-07-14

Task: AGENT-330

## Decision

No internal Nu row is fit-admissible today. The admitted Salt2-4 upcomer evidence is useful as a physics/admission diagnostic, but every current row remains in a recirculating regime and the thermal gate forbids internal Nu from absorbing heater, cooler, passive loss, wall storage, branch mixing, radiation, or sign residuals.

## Observed Facts

- Admitted diagnostic cases span Re_upcomer 71.125-134.883; all 3 rows are classified as recirculation_cell_observed.
- Backflow fraction decreases with Re across Salt2-4, from 0.277778 to 0.171875, but it does not approach zero in the admitted evidence.
- Ri_median remains above one in all rows, from 1.497987 to 2.633785.
- Pr decreases while Ra/Gr increase across the same monotone case sequence. With only three recirculating points and no ordinary-pipe anchor, those correlations are not separable into a threshold law.
- Direct wall-bulk or wall-core Delta T and Gz are not present in the upcomer onset source tables. They are carried as blocked metrics, not inferred.
- The lit-review CFD validity package marks left_upper_leg and upper_leg coefficient names as section-effective only under reverse/recirculation proxies.
- CFD rcExternalTemperature wallHeatFlux includes radiation where that boundary condition is used; there is no separate exported qr term to add to an internal-Nu residual.

## Interpretation

Upcomer recirculation is now an admission rule: when backflow_fraction >= 0.10, Ri_median >= 1, reverse-flow area/mass is material, or recirculation_zone_flag is yes, single-stream `Nu`, `f_D`, and `K` labels are invalid. Use section-effective or diagnostic names and keep those rows out of closure fitting.

Current correlations are qualitative only: higher Re coincides with lower backflow fraction and lower recirculation intensity over Salt2-4, while the entire observed range remains recirculating. That supports a recirculation caveat and naming rule, not a calibrated onset threshold or a transferable internal-Nu closure.

## Blocked Missing Metrics

- Ordinary-pipe or transition anchors bracketing the onset.
- Direct upcomer wall-bulk or wall-core Delta T over the same time window as the flow metrics.
- Gz or equivalent thermal-development metric.
- Secondary velocity fraction and plane-resolved reverse mass/area fractions.
- Mesh/time uncertainty for the recirculation diagnostics.
- Terminal corrected-Q admission for any candidate cases used beyond diagnostic screening.

## Next Extraction Request

Extract matched vector and thermal planes at upcomer inlet, midpoint, and outlet for each admitted/candidate case: reverse area fraction, reverse mass fraction, secondary velocity fraction, mass-flux-weighted bulk temperature, area-weighted wall temperature, local wallHeatFlux, Re, Pr, Ri, Ra/Gr, Gz, and the exact time window. Add cases near Re 150, 200, and 250, plus a non-recirculating or transition anchor if available, before any internal-Nu fit gate is reopened.

## Outputs

- `upcomer_recirculation_onset_conditions.csv`
- `coefficient_naming_rules_for_recirculation.csv`
- `blocked_missing_metrics.csv`
- `source_manifest.csv`
- `summary.json`
