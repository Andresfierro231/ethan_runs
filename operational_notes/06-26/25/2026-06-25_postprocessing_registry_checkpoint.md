# Ethan PostProcessing Registry Checkpoint

Date: `2026-06-25`
Checkpoint task: `AGENT-133`

## Purpose

This is the restart-safe handoff note for the Ethan OpenFOAM postProcessing
registry work completed on `2026-06-25`.

It captures:

- what was implemented
- what completed successfully on the compute node
- where the outputs live
- current environment constraints
- the one known discrepancy already surfaced
- the most likely tomorrow follow-up items

This note is intentionally self-contained so the work can resume tomorrow
without re-reading the whole terminal thread.

## Big Picture

The registry-local postProcessing pipeline is operational end-to-end for all
currently registered Ethan CFD runs.

Completed today:

- reusable aggregation pipeline
- per-run registry storage in CSV and SQLite
- grouped wall-heat aggregation
- TP plot CLI
- TW plot CLI
- velocity-profile plot CLI
- full all-`13`-case aggregation sweep
- full all-`13`-case TP/TW plot sweeps
- full all-`13`-case final-timestep velocity-profile plot sweep
- `piv_slab_velocity` math note

## Main deliverables

### Scripts

- [aggregate_registered_postprocessing.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/extract/aggregate_registered_postprocessing.py:1)
- [postprocessing_registry_common.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/extract/postprocessing_registry_common.py:1)
- [plot_temperature_probes.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/plot_temperature_probes.py:1)
- [plot_wall_temperature_probes.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/plot_wall_temperature_probes.py:1)
- [plot_velocity_profiles.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/plot_velocity_profiles.py:1)

### Tests

- [test_postprocessing_registry.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/extract/test_postprocessing_registry.py:1)
- [test_postprocessing_plots.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/test_postprocessing_plots.py:1)

### Provenance / summaries

- [2026-06-25_ethan_postprocessing_registry_pipeline.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-25_ethan_postprocessing_registry_pipeline.json:1)
- [2026-06-25_piv_slab_velocity_math.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_piv_slab_velocity_math.md:1)
- [coordinator-implementer-writer-postprocessing-registry-pipeline.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/journal/2026-06-25/coordinator-implementer-writer-postprocessing-registry-pipeline.md:1)

## What the pipeline writes

For each registered run, under:

```text
registry/<bucket>/<source_owner>/<case_id>/<run_name>/
```

the pipeline writes:

- `aggregates/postprocessing_case_long.csv`
- `aggregates/wall_heat_flux_grouped.csv`
- `aggregates/case_summary.csv`
- `aggregates/case_summary.json`
- `aggregates/postprocessing.sqlite`
- `aggregation_manifest.json`

Family/global indexes:

- [registry/_all_postprocessing_runs.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/registry/_all_postprocessing_runs.csv:1)
- [registry/_all_postprocessing_runs.sqlite](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/registry/_all_postprocessing_runs.sqlite:1)
- `registry/salt1/_family_index.{csv,sqlite}`
- `registry/salt2/_family_index.{csv,sqlite}`
- `registry/salt3/_family_index.{csv,sqlite}`
- `registry/salt4/_family_index.{csv,sqlite}`
- `registry/water1/_family_index.{csv,sqlite}`
- `registry/water2/_family_index.{csv,sqlite}`
- `registry/water3/_family_index.{csv,sqlite}`
- `registry/water4/_family_index.{csv,sqlite}`

## Important design decisions that are already implemented

### 1. Fast format is SQLite, not Parquet

Reason:

- current environment does not have `pyarrow`
- current environment does not have `pandas`

So the “fast computation / plotting” storage format landed as SQLite.

### 2. Velocity profiles are excluded from the main long table

The user requested that `velocity_profile` not be carried in the main long
table.

Current behavior:

- `postprocessing_case_long.csv` does **not** include `velocity_profile` rows
- `postprocessing.sqlite` main table does **not** include `velocity_profile`
  rows
- the velocity-profile plotter reads raw
  `postProcessing/velocity_profiles/<time>/*.xy` data directly by default

This materially reduced sweep cost and output bloat.

### 3. Wall-heat grouped output is separate and preserved

The second requested aggregation is implemented as:

- `wall_heat_flux_grouped.csv`

with:

- `total_Q_postProc` as the first column

### 4. `mdot` discrepancy detection is active

Case summaries include:

- `mdot_all_same`
- `mdot_consensus_kg_s`
- `mdot_abs_spread_kg_s`
- `mdot_discrepancy_note`

The tolerance currently used is:

- `MDOT_TOLERANCE_KG_S = 1e-6`

## Full aggregation status

The full foreground sweep completed successfully on the compute node.

Completion timestamp from the final manifest:

- `2026-06-25T16:44:17-05:00`

Processed source ids:

1. `val_salt_test_2_coarse_mesh_laminar`
2. `val_water_test_1_coarse_mesh_laminar`
3. `val_water_test_2_coarse_mesh_laminar`
4. `val_water_test_3_coarse_mesh_laminar`
5. `val_water_test_4_coarse_mesh_laminar`
6. `viscosity_screening_salt_test_1_jin_coarse_mesh`
7. `viscosity_screening_salt_test_1_kirst_coarse_mesh`
8. `viscosity_screening_salt_test_2_jin_coarse_mesh`
9. `viscosity_screening_salt_test_2_kirst_coarse_mesh`
10. `viscosity_screening_salt_test_3_jin_coarse_mesh`
11. `viscosity_screening_salt_test_3_kirst_coarse_mesh`
12. `viscosity_screening_salt_test_4_jin_coarse_mesh`
13. `viscosity_screening_salt_test_4_kirst_coarse_mesh`

## Quick validation results

Validation checks already completed:

- `13` global index rows present
- no missing indexed output files
- `wall_heat_flux_grouped.csv` header order correct
- normalized long table excludes `velocity_profile`
- real-output TP/TW plot sweeps completed for all `13` runs
- real-output final-time velocity-profile plot sweep completed for all `13`
  runs

### One known `mdot` discrepancy case

Exactly one case was flagged as discrepant:

- `val_water_test_4_coarse_mesh_laminar`

Observed spread:

- `1.2759499999990404e-06 kg/s`

This is only slightly above the current tolerance, but it is intentionally
being surfaced rather than hidden.

## Plotting status

### Temperature probe plots

Real-output sweep completed for all `13` cases.

Per case output:

- `plots/temperature_probes/svg/registry_tp_default.svg`
- `plots/temperature_probes/png/registry_tp_default.png`

Final counts:

- `13` TP `svg`
- `13` TP `png`

### Wall temperature plots

Real-output sweep completed for all `13` cases.

Per case output:

- `plots/wall_temperature_probes/svg/registry_tw_default.svg`
- `plots/wall_temperature_probes/png/registry_tw_default.png`

Final counts:

- `13` TW `svg`
- `13` TW `png`

### Velocity-profile plots

The velocity plotter supports:

- explicit times via `--times`
- latest `N` times via `--last-n`

An optimization was added today so the default raw-data path only reads the
selected profile times instead of the full profile history.

Final-time sweep completed for all `13` cases with:

```bash
python3 tools/analyze/plot_velocity_profiles.py \
  --source-id <source_id> \
  --output-name registry_velocity_final \
  --last-n 1
```

Per case output:

- `plots/velocity_profiles/svg/registry_velocity_final.svg`
- `plots/velocity_profiles/png/registry_velocity_final.png`

Final counts:

- `13` velocity-profile `svg`
- `13` velocity-profile `png`

## `piv_slab_velocity` math status

The separate report is already written:

- [2026-06-25_piv_slab_velocity_math.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_piv_slab_velocity_math.md:1)

Bottom line from that note:

- `piv_slab` is a `cellZone` created by `boxToCell`
- OpenFOAM first constructs `magU = |U|`
- then `volFieldValue` with `operation volAverage` computes:
  - `⟨Ux⟩`
  - `⟨Uy⟩`
  - `⟨Uz⟩`
  - `⟨|U|⟩`
  - `⟨T⟩`

Important interpretation boundary:

- reported `magU` is `⟨|U|⟩`, not `|⟨U⟩|`

## Environment constraints that matter tomorrow

### Python environments

- `python3.11`:
  - good for aggregation/tests
  - does **not** have `matplotlib`
- `python3`:
  - has `matplotlib`
  - used for real plotting runs

### Dependency constraints

- no `pyarrow`
- no `pandas`

That is why the fast store is SQLite instead of Parquet.

## Repro commands

### Rebuild all registry aggregates

```bash
python3.11 tools/extract/aggregate_registered_postprocessing.py
```

### Rebuild one selected run

```bash
python3.11 tools/extract/aggregate_registered_postprocessing.py \
  --source-id viscosity_screening_salt_test_2_kirst_coarse_mesh
```

### Plot one TP figure

```bash
python3 tools/analyze/plot_temperature_probes.py \
  --source-id viscosity_screening_salt_test_2_kirst_coarse_mesh \
  --output-name my_tp_plot \
  --include TP1 TP4
```

### Plot one TW figure

```bash
python3 tools/analyze/plot_wall_temperature_probes.py \
  --source-id viscosity_screening_salt_test_2_kirst_coarse_mesh \
  --output-name my_tw_plot \
  --include TW1 TW5
```

### Plot specified velocity-profile times

```bash
python3 tools/analyze/plot_velocity_profiles.py \
  --source-id viscosity_screening_salt_test_2_kirst_coarse_mesh \
  --output-name my_velocity_plot \
  --times 586.56 600.0
```

### Plot final-time velocity profile

```bash
python3 tools/analyze/plot_velocity_profiles.py \
  --source-id viscosity_screening_salt_test_2_kirst_coarse_mesh \
  --output-name my_velocity_final \
  --last-n 1
```

## Most likely tomorrow TODOs

### High-value follow-up

- [ ] Review the single flagged `mdot` discrepancy case:
  - `val_water_test_4_coarse_mesh_laminar`
  - decide whether the tolerance should remain `1e-6 kg/s` or be relaxed
- [ ] Spot-check a few `case_summary.csv` and `wall_heat_flux_grouped.csv`
  files for physical reasonableness, not just file existence
- [ ] Decide whether a user-facing batch wrapper script should be added for:
  - TP plots across all runs
  - TW plots across all runs
  - final-time velocity plots across all runs
- [ ] Decide whether the grouped wall-heat output needs its own dedicated plot
  or report builder next

### Format / storage decisions

- [ ] Decide whether SQLite is sufficient as the defended “fast” format, or
  whether a Parquet-capable environment should be introduced later
- [ ] If Parquet is required, add an environment with `pyarrow` or `pandas`
  and extend the writer path rather than changing the current SQLite workflow

### Documentation / interpretation

- [ ] Decide whether the `piv_slab_velocity` math note should remain in
  `operational_notes/` or be promoted into a report package
- [ ] If later analysis wants experimental-style PIV mass-flow surrogates,
  define the exact density convention explicitly rather than inferring it from
  the existing `piv_slab_velocity` outputs

### Potential enhancements

- [ ] Add a compact batch report summarizing:
  - latest `total_Q_postProc`
  - latest slab `magU`
  - latest TP average
  - `mdot` agreement flag
  - grouped wall-heat partitions
- [ ] Consider a separate lightweight velocity-profile cache if repeated
  cross-run profile plotting becomes common

## If tomorrow starts with “where do I look first?”

Start here:

1. [2026-06-25_ethan_postprocessing_registry_pipeline.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-25_ethan_postprocessing_registry_pipeline.json:1)
2. [registry/_all_postprocessing_runs.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/registry/_all_postprocessing_runs.csv:1)
3. [coordinator-implementer-writer-postprocessing-registry-pipeline.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/journal/2026-06-25/coordinator-implementer-writer-postprocessing-registry-pipeline.md:1)
4. [2026-06-25_piv_slab_velocity_math.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_piv_slab_velocity_math.md:1)
5. this checkpoint note

## Short restart summary

The important practical state is:

- the aggregation pipeline is done
- all `13` runs were aggregated successfully
- TP/TW real plots exist for all `13` runs
- final-time velocity-profile plots exist for all `13` runs
- `velocity_profile` is intentionally excluded from the main long table
- the grouped wall-heat export exists as a separate table
- one marginal `mdot` discrepancy case has already been identified
- the `piv_slab_velocity` math has been documented

Tomorrow should start from interpretation and packaging decisions, not from
pipeline implementation or rerunning blind diagnostics.
