# Presentation Takeaways

Date: `2026-06-23`

## Five points to lead with

1. The repo now has a canonical `13`-run Ethan CFD campaign in the cross-model
   publication tree, with per-run reports plus one uniform cross-run summary
   backbone.
2. The Salt-family now has a reusable detailed transport layer, not just
   monitor-only comparisons: streamwise heat-loss, parasitic-loss, azimuthal
   transport, and first-pass boundary-layer outputs exist in durable packages.
3. The paper/presentation layer is now filtered through an explicit scrutiny
   gate, so we can separate safe branches and mechanisms from contextual-only
   or excluded outputs.
4. The first Salt-informed 1D model now has a clearer closure menu: keep it
   development-aware, branch-aware, and family-aware rather than assuming fully
   developed friction or `Nu` everywhere.
5. The bounded local bakeoff is now complete, and it still says the current
   defended readable 1D surface is not yet predictive enough.

## Four caveats to say out loud

1. The canonical all-run campaign is still monitor-first and is not yet a
   pressure-validation campaign.
2. Direct internal-HTC / direct-`Nu` evidence remains narrow; the best current
   direct branch evidence is still limited rather than loop-wide.
3. `p_rgh` is not dynamic pressure. The repo now shows that directly, but the
   talk should not treat a `p_rgh` curve as a dynamic-loss curve.
4. The external refreshed `Fluid` replay is still active work, so today’s
   local 1D result is a bounded negative result on top of a stale June 19
   readable bundle.

## Best staged figures for this week

All staged deck assets now live under:

- `reports/2026-06-23_presentation/figures/`

Main deck:

- `01_title_salt_dashboard_overview`
- `02_loop_heat_loss_comparison`
- `03_bounded_pressure_closure`
- `04_prgh_vs_qdyn_salt2_kirst`
- `05_salt_hydraulic_agreement`
- `06_salt_branch_usability`
- `07_salt_heat_loss_partition`
- `08_primary_scenario_metric_heatmap`
- `09_primary_branch_development`
- `10_current_1d_gap_summary`

Backups:

- `A_representative_friction_and_pressure`
- `B_primary_best_sensor_parity`
- `C_salt2_kirst_redevelopment_followon`
- `D_salt1to4_metric_cards`

Canonical source paths, provenance packages, and assumption notes live in:

- `reports/2026-06-23_presentation/figures/figure_manifest.csv`

## Current quantified prediction picture

- CFD-versus-experiment remains strongest for water:
  mean wall-temperature RMSE `2.22 K` for water versus `9.30 K` for salt
- external-loss absolute error is also better for water:
  `5.95%` for water versus `21.06%` for salt
- the refreshed local bakeoff still shows poor defended 1D predictiveness:
  best full-coverage readable scenario
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
  gives mean energy-loss mismatch `11.27%` of heater, mean wall RMSE
  `62.79 K`, mean centerline RMSE `62.69 K`, and mean mass-flow error
  `26.69%`
- on the readable Salt `1-4` `Jin` progression for that same defended row,
  the miss trends are:
  `Salt 1 = 15.99% / 65.40 K / 65.61 K / 21.74%`,
  `Salt 2 = 8.43% / 63.82 K / 63.67 K / 25.03%`,
  `Salt 3 = 10.26% / 66.55 K / 65.61 K / 27.69%`,
  `Salt 4 = 12.51% / 69.18 K / 67.68 K / 29.90%`
  for `energy / TW / TP / mdot`
- case breakdown for that defended row:
  `Salt 1 Kirst = 16.01%` heater error, `65.31 K` TW RMSE,
  `65.24 K` TP RMSE, `25.45%` mass-flow error;
  `Salt 2 Kirst = 8.92%`, `64.65 K`, `64.78 K`, `34.41%`;
  `Salt 2 Val = 8.89%`, `58.40 K`, `58.05 K`, `20.21%`
- Salt 1 is the only primary frozen case where the current hybrid row wins
  overall, and even there the gain is only relative rather than good enough
- Salt 2 still prefers the baseline `1.0 in` / radiation-on row overall, while
  the hybrid/profile-descriptor family remains under-covered with only `3`
  primary comparison rows total
- hybrid only wins one observable lane provisionally:
  best hybrid mean mass-flow error is `19.55%`, but that row covers only `1`
  primary case and still does not beat the defended baseline on mean
  temperature error
- if the target CFD insulation is globally `1.4 in`, the present defended
  winner should be described as a bounded surrogate rather than a final replay
  verdict because no readable global `1.4 in` Salt scenario is currently
  published
- `energy error` in this package means
  `|(Q_removed + Q_ambient)_1D - (Q_removed + Q_ambient)_CFD| / |Q_heater,CFD|`
  rather than an experiment-side discrepancy

Presentation-local support files for this section:

- `reports/2026-06-23_presentation/1d_model_slide_sequence.md`
- `reports/2026-06-23_presentation/1d_model_results_tables.md`
- `reports/2026-06-23_presentation/1d_model_setup_documentation.md`

## Current admitted correlation set

- straight friction fit:
  `log(f_D) = 5.2316378122 - 0.9477837868 log(Re) + 2.9210668439 I[test_section_span]`
- direct Salt `Nu(Re)` only on `left_lower_leg`:
  `log(Nu) = -3.0042709988 + 0.9607621733 log(Re)`
- primary thermal surface: `UA'(x)` on the safe subset
- secondary thermal surface: `HTC(x)` on the same subset
- feature `K_eff` is reopened only as `provisional_defended`
- current retained feature-path coverage is `21` fit-used rows out of `45`,
  with `24` rows still excluded by nonpositive path feature excess

## Next analysis lane

- land the refreshed external replay so the same local scorecard can be rerun
  on a non-stale 1D surface
- keep the current local bakeoff as the working truth for which readable
  scenarios fail by energy balance, TW, TP, and mass flow
- then run a bounded bakeoff of alternative friction and HTC/Nu correlations
  rather than opening a broad uncontrolled correlation search
