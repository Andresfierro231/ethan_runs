# 1D Model Results Tables

Date: `2026-06-23`

These are presentation-local tables for the current published June 23 1D
comparison stack. They summarize:

- `reports/2026-06-23_ethan_frozen_state_1d_validation/`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/`

## Table 1: Overall Scenario Comparison

Use this table when the slide needs one compact ranking summary rather than the
full heatmap figure.

| Scenario | Family | Insulation | Radiation | Mean energy [% heater] | Mean `T_w` RMSE [K] | Mean `T_p` RMSE [K] | Mean mdot error vs CFD [%] | Coverage note |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | baseline | `1.0 in` | on | `11.27` | `62.79` | `62.69` | `26.69` | best full-coverage readable row |
| `ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1` | hybrid | `1.0 in` | on | `16.01` | `66.40` | `65.99` | `19.55` | better mdot than baseline, but only `1` primary readable row |
| `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0` | baseline | `1.0 in` | off | `11.27` | `93.58` | `93.77` | `50.91` | full coverage but much worse temperatures |

Interpretation:

- The defended winner is the baseline `1.0 in` radiation-on row because it is
  the best full-coverage readable scenario.
- The hybrid row is interesting for mass flow, but it does not yet have enough
  readable breadth to be defended as the best global choice.

## Table 2: Strict Published Case-By-Case Comparison

This is the cleanest table to place directly on a slide.

| CFD reference case | 1D scored scenario | Mean energy [% heater] | `T_w` RMSE [K] | `T_p` RMSE [K] | mdot error vs CFD [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| `Salt 1 Kirst` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `16.01` | `65.31` | `65.24` | `25.45` |
| `Salt 2 Kirst` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `8.92` | `64.65` | `64.78` | `34.41` |
| `Salt 2 Val` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `8.89` | `58.40` | `58.05` | `20.21` |

Interpretation:

- Every published strict comparison case still shows large temperature error.
- Mass-flow error remains large even where energy mismatch is single-digit
  percent of heater.

## Table 2B: Salt 1-4 Progression Cards On One Consistent Scenario

This is the table behind the presentation-local `D_salt1to4_metric_cards`
backup figure. It uses the readable `Jin` progression because that is the only
current four-case Salt family span on one defended full-coverage scenario.

| CFD reference case | 1D scored scenario | Mean energy [% heater] | `T_w` RMSE [K] | `T_p` RMSE [K] | mdot error vs CFD [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| `Salt 1 Jin` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `15.99` | `65.40` | `65.61` | `21.74` |
| `Salt 2 Jin` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `8.43` | `63.82` | `63.67` | `25.03` |
| `Salt 3 Jin` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `10.26` | `66.55` | `65.61` | `27.69` |
| `Salt 4 Jin` | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` | `12.51` | `69.18` | `67.68` | `29.90` |

Interpretation:

- The temperature and mass-flow miss worsen again by Salt `3-4`.
- Energy mismatch does not collapse to zero even where the temperature miss is
  only moderately worse, which suggests the current problem is not just one
  bulk heat-loss scalar.

## Table 3: Heater-To-Fluid Partition From The CFD Side

This is the most compact table for explaining why the heat-input contract still
matters.

| Case | Heater config [W] | Test-section source [W] | CFD heater net to fluid [W] | Heater power not reaching fluid [W] | CFD removed [W] | CFD ambient [W] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Salt 1 Kirst` | `232.3` | `37.0` | `213.09` | `19.21` | `135.60` | `167.81` |
| `Salt 2 Kirst` | `265.7` | `37.0` | `243.66` | `22.04` | `136.35` | `188.09` |

Interpretation:

- The reduced-order model should not assume that all configured heater power
  reaches the fluid.
- The CFD side already suggests a first correction target of roughly
  `19-22 W` heater-to-fluid gap on these two representative published cases.

## Energy Error Definition

For every 1D-vs-frozen-CFD row in this package:

- `Q_lost,1D = qhx_total_W + qambient_total_W`
- `Q_lost,CFD = cfd_removed_w + cfd_ambient_w`
- `energy_error_w = Q_lost,1D - Q_lost,CFD`
- `energy_error_pct_of_heater = 100 * abs(energy_error_w) / abs(cfd_heater_w)`

Interpretation:

- This is a heater-normalized total-loss mismatch against the frozen CFD heat
  ledger.
- It is not a separate experimental comparison and it is not a signed
  efficiency metric.
- The absolute value is used in the reported percentage score, so `11.27%`
  means the 1D total lost heat misses the CFD total lost heat by `11.27%` of
  the CFD heater net-to-fluid power.

## Table 4: Presentation-Friendly Summary Of What The Current 1D Result Means

| Question | Current answer |
| --- | --- |
| Is the current local 1D model predictive enough? | No. The best full-coverage row still misses badly on energy, wall temperature, centerline temperature, and mass flow. |
| Is the current result still useful? | Yes. The miss pattern is now quantified and branch-localized, so the next model changes are constrained rather than speculative. |
| What is the strongest current direct thermal closure lane? | `left_lower_leg` only. |
| What branch most clearly needs special treatment? | `upcomer`, because it remains sensitivity-only and likely needs a buoyancy-aware submodel. |
| What setup mismatch is still unresolved? | The readable bundle still does not publish a globally matched `1.4 in` Salt scenario. |
