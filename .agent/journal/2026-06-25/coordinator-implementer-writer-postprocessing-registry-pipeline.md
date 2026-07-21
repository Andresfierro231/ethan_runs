# AGENT-130

## Research question

Can the repo emit a registry-local postProcessing aggregation and plotting path
that reads the registered OpenFOAM monitor outputs directly, writes durable
per-run CSV plus fast-query storage, flags mdot disagreement clearly, and keeps
the TP/TW/velocity-profile figures reusable from the command line?

## Observed output

- Added a new extraction helper stack in
  `tools/extract/postprocessing_registry_common.py` and
  `tools/extract/aggregate_registered_postprocessing.py`.
- Added reusable plotting CLIs in:
  - `tools/analyze/plot_temperature_probes.py`
  - `tools/analyze/plot_wall_temperature_probes.py`
  - `tools/analyze/plot_velocity_profiles.py`
- Added focused automated coverage in:
  - `tools/extract/test_postprocessing_registry.py`
  - `tools/analyze/test_postprocessing_plots.py`
- A real-case smoke aggregation completed for
  `viscosity_screening_salt_test_2_kirst_coarse_mesh` and wrote:
  - `registry/salt2/ethan_modern_runs_staged/salt_test_2_kirst/viscosity_screening_salt_test_2_kirst_coarse_mesh/aggregates/postprocessing_case_long.csv`
  - `registry/salt2/ethan_modern_runs_staged/salt_test_2_kirst/viscosity_screening_salt_test_2_kirst_coarse_mesh/aggregates/wall_heat_flux_grouped.csv`
  - `registry/salt2/ethan_modern_runs_staged/salt_test_2_kirst/viscosity_screening_salt_test_2_kirst_coarse_mesh/aggregates/case_summary.csv`
  - `registry/salt2/ethan_modern_runs_staged/salt_test_2_kirst/viscosity_screening_salt_test_2_kirst_coarse_mesh/aggregates/postprocessing.sqlite`
  - `registry/salt2/ethan_modern_runs_staged/salt_test_2_kirst/viscosity_screening_salt_test_2_kirst_coarse_mesh/aggregation_manifest.json`
- The same smoke run updated:
  - `registry/_all_postprocessing_runs.csv`
  - `registry/_all_postprocessing_runs.sqlite`
  - `registry/salt2/_family_index.csv`
  - `registry/salt2/_family_index.sqlite`
- Real plot smokes completed from the generated aggregate:
  - `plots/temperature_probes/{svg,png}/real_tp_smoke.*`
  - `plots/velocity_profiles/{svg,png}/real_velocity_smoke.*`

## Interpretation

- The pipeline is additive and keeps all writes under `registry/`, which
  matches the requested destination layout.
- The fast-format implementation had to shift from Parquet to SQLite because
  the active environment lacks both `pyarrow` and `pandas`. SQLite still fits
  the fast-query / plotting use case and preserves append-safe semantics.
- The CLI layer is reusable as requested:
  TP/TW accept include/exclude plus axis/legend controls, and the
  velocity-profile plotter supports last-`N` or requested times with matched
  time annotation in the figure.
- The real-case Salt 2 Kirst smoke shows the aggregator can digest an actual
  OpenFOAM `postProcessing` tree and write both grouped heat data and a full
  normalized monitor table.

## Contradictions / constraints

- `python3.11` is suitable for parser/unit tests here, but it does not have
  `matplotlib`; the plot CLI validation had to use `python3`.
- A full all-case run was not executed in this turn. The real Salt 2 Kirst
  smoke succeeded, but the retained velocity-profile history makes a full
  registry sweep materially longer than the bounded smoke validation used here.

## Next suggested actions

- Run `python3.11 tools/extract/aggregate_registered_postprocessing.py` when
  you want the full registered case population emitted under `registry/`.
- If Parquet remains a requirement, add an environment with `pyarrow` or
  `pandas` and extend the writer path in
  `tools/extract/postprocessing_registry_common.py`.
- Open a separate board task for the `piv_slab_velocity` math write-up, as
  requested.

## 2026-06-25 addendum

### Observed output

- The normalized aggregate was updated so `velocity_profile` rows are no
  longer written into `postprocessing_case_long.csv` or the main
  `postprocessing.sqlite` table.
- `tools/analyze/plot_velocity_profiles.py` now loads raw
  `postProcessing/velocity_profiles/**.xy` files directly unless `--input-csv`
  is explicitly provided.
- The aggregation CLI now prints per-case progress lines, which makes
  detached logging usable during long registry sweeps.
- A detached tmux session named `agent130_postproc` was started on the compute
  node at `2026-06-25 14:22 CDT` with log path
  `tmp/postprocessing_runs/aggregate_registered_postprocessing_2026-06-25_v2.log`.
- Immediate log confirmation showed:
  `[1/13] aggregating val_salt_test_2_coarse_mesh_laminar`

### Interpretation

- Removing velocity profiles from the main long table should substantially
  reduce both registry output size and all-case sweep time while preserving the
  reusable velocity-profile figure workflow.
- The requested second aggregation for wall heat remains part of the emitted
  per-run package and was not deferred.

### Validation

- `python3.11 -m unittest tools.extract.test_postprocessing_registry tools.analyze.test_postprocessing_plots`
- `python3.11 -m py_compile tools/extract/postprocessing_registry_common.py tools/extract/aggregate_registered_postprocessing.py tools/extract/test_postprocessing_registry.py tools/analyze/plot_velocity_profiles.py`

## 2026-06-25 completion addendum

### Observed output

- The full foreground aggregation sweep completed successfully for all `13`
  registered cases.
- `registry/_all_postprocessing_runs.csv` and
  `registry/_all_postprocessing_runs.sqlite` were refreshed at
  `2026-06-25 16:44 CDT`.
- A bounded validation pass confirmed:
  - `13` global index rows
  - no missing `normalized_csv`, `heat_grouped_csv`, `summary_csv`, or
    `sqlite_db` targets
  - `wall_heat_flux_grouped.csv` retains `total_Q_postProc` as column `1`
  - normalized long tables do not include `velocity_profile` rows
- `mdot` discrepancy detection flagged exactly one case:
  `val_water_test_4_coarse_mesh_laminar`, with spread
  `1.2759499999990404e-06 kg/s`.
- Real-output temperature and wall-temperature plotting sweeps completed for
  all `13` cases using:
  - `python3 tools/analyze/plot_temperature_probes.py --source-id ... --output-name registry_tp_default`
  - `python3 tools/analyze/plot_wall_temperature_probes.py --source-id ... --output-name registry_tw_default`
- Final plot counts:
  - `13` TP `svg`
  - `13` TP `png`
  - `13` TW `svg`
  - `13` TW `png`

### Interpretation

- The registry-local pipeline is operational end-to-end for the currently
  registered Ethan case set.
- The `mdot` discrepancy flag is functioning as intended and already surfaced
  one marginal disagreement case for later review.
- The default TP/TW plotting workflow is now validated on real aggregate
  outputs rather than only synthetic smoke data.

## 2026-06-25 velocity-profile plotting addendum

### Observed output

- `tools/analyze/plot_velocity_profiles.py` was revised so the default raw
  plotting path reads only the matched/selected time directories instead of
  loading every historical velocity-profile file for a run.
- After that optimization, a real-output final-timestep plotting sweep
  completed successfully for all `13` registered cases using:
  - `python3 tools/analyze/plot_velocity_profiles.py --source-id ... --output-name registry_velocity_final --last-n 1`
- Final output counts:
  - `13` velocity-profile `svg`
  - `13` velocity-profile `png`

### Interpretation

- The velocity-profile CLI now matches the intended operational use much
  better: explicit times or `--last-n 1` no longer pay the full historical
  scan cost for each run.
