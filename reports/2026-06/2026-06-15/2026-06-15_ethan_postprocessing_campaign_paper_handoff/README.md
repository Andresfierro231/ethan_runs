# Ethan postprocessing campaign paper handoff

Date: `2026-06-15`

## Purpose

This handoff translates the completed Ethan postprocessing queue wave into a
paper-facing summary that can be reused while drafting a scientific manuscript.
It does not replace the canonical campaign package. Instead, it points drafting
back to the review-clean evidence package at:

`../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/`

Use that campaign as the citation backbone for figures, tables, and per-run
interpretation. Use this note as the compact map of what the package supports,
what it does not support, and how to frame the results conservatively.

Canonical DMDC mirror:

`../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/reports/2026-06-15_paper_handoff.md`

## Canonical evidence package

Primary campaign reports:

- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/reports/executive_summary.md`
- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/reports/technical_analysis.md`
- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/reports/methodology.md`

Primary campaign tables:

- `.../data/run_index.csv`
- `.../data/readiness_matrix.csv`
- `.../data/cross_run_summary.csv`
- `.../data/runtime_final_time_by_run.csv`
- `.../data/temperature_probe_avg_by_run.csv`
- `.../data/comparison_tw_rmse_by_run.csv`
- `.../data/heat_transfer_ambient_proxy_by_run.csv`

Key provenance notes:

- `journals/2026-06/2026-06-09_ethan_runs.md`
- `journals/2026-06/2026-06-12_ethan_runs.md`
- `../cfd-modeling-tools/cross_model_comparison/journals/2026-06/2026-06-12_workflow_journal.md`
- `../cfd-modeling-tools/cross_model_comparison/operational_notes/2026-06-12_ethan_postprocessing_all_runs_v1/CHECKPOINT.md`
- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/TODO.md`

## Dataset definition

- Registered CFD runs carried into the campaign: `13`
- Excluded from this synthesis: the separate `inventory_only` row
- Fluid-family split:
  - `4` water runs
  - `9` salt-family runs
- Runtime-state split:
  - `1` `running`
  - `10` `terminated`
  - `2` `completed`
- Workflow-readiness split:
  - `3` `comparison_candidate`
  - `10` `convergence_audit_required`

The campaign deliberately keeps all registered runs instead of pruning
non-converged or continuation-affected rows. This is a provenance strength, but
it means manuscript text must preserve the readiness labels instead of
flattening them into one uniform “validated CFD” set.

## What the package contains

For each run, the canonical campaign provides:

- cleaned CSV tables behind every cross-run and per-run figure
- SVG, PDF, and PGFPlots/TikZ figure outputs
- a per-run artifact map
- a per-run executive summary
- a per-run technical analysis

At the campaign level, it provides:

- one uniform run index and readiness table
- one cross-run summary table with runtime, validation, and thermal metrics
- top-level executive, technical, and methodology reports
- a canonical monitor-first interpretation contract that stays consistent across
  water, Salt Jin, Salt Kirst, and the live Salt 2 continuation

## Manuscript-safe quantitative summary

The current package supports the following high-level quantitative framing from
`data/cross_run_summary.csv`:

| Metric | Water family | Salt family |
| --- | --- | --- |
| Run count | `4` | `9` |
| Mean wall-temperature RMSE | `2.22 K` | `9.30 K` |
| Mean external-loss absolute error | `5.95%` | `21.06%` |
| Mean average `y+` | `2.35` | `0.65` |

Campaign extrema:

- Best wall-temperature RMSE:
  `val_water_test_1_coarse_mesh_laminar` at about `1.67 K`
- Worst wall-temperature RMSE:
  `viscosity_screening_salt_test_1_jin_coarse_mesh` at about `17.80 K`
- Best external-loss absolute error:
  `val_water_test_4_coarse_mesh_laminar` at about `4.63%`
- Worst external-loss absolute error:
  `viscosity_screening_salt_test_1_jin_coarse_mesh` at about `27.36%`

Current `comparison_candidate` rows:

- `val_salt_test_2_coarse_mesh_laminar`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`

These numbers support a family-level split more clearly than a blanket
convergence story: water rows agree better with experiment on the current
thermal metrics, while the salt-family rows contain the strongest workflow
maturity rows but the weaker validation averages.

## Interpretation for paper drafting

The strongest scientifically defensible use of this package is as a
monitor-derived comparison backbone. It is well suited for:

- documenting what CFD evidence exists across the 13 registered Ethan cases
- comparing fluid-family trends in monitor-derived thermal behavior
- separating workflow maturity from validation quality
- citing exact per-run tables, figures, and artifact maps when discussing one
  case in detail

The strongest current comparison story is:

1. The repository now holds one canonical postprocessing package for all 13
   Ethan cases.
2. Water rows remain the cleanest direct-validation context on the current
   thermal metrics.
3. Salt Kirst rows provide the strongest workflow-maturity comparison anchors.
4. The live base Salt 2 continuation remains useful for heat-partition context,
   but not as a synchronized terminal-state validation anchor.

This framing aligns with the June 9 heat audit, which found that water rows
look broadly self-consistent while the salt family carries a persistent
under-loss / wall-temperature-miss signal.

## Claim boundaries that must stay explicit

### Pressure

Do not present this v1 package as a pressure-validation or pressure-history
campaign. The native labeled monitor stack used here does not provide direct
pressure histories for the baseline evidence path. Pressure remains a declared
future-work boundary in both the campaign `TODO.md` and the June 12 workflow
journal.

### Readiness versus validation

Do not equate `comparison_candidate` with “fully validated” or “converged final
result.” In this campaign, the three `comparison_candidate` rows do not share
the same maturity state:

- `viscosity_screening_salt_test_2_kirst_coarse_mesh` is the strongest
  workflow-maturity anchor because it is completed, converged, and described as
  essentially steady.
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` is completed but still
  carries a `not_steady_enough` caveat.
- `val_salt_test_2_coarse_mesh_laminar` is still a live continuation row with
  mixed evidence horizons.

### Salt 2 continuation

The repaired live Salt 2 row is now internally honest, but it is still mixed in
time base:

- runtime metadata through `3871 s`
- heat history through `8602 s`
- probe / velocity context through `1724 s`

Manuscript text can use that row for caveated continuation context, heat
partition framing, and comparison completeness. It should not use it as if all
observables came from one synchronized converged endpoint.

### Field reconstruction

This package is monitor-first. It does not claim that new ParaView field
reconstruction, pressure-slice analysis, or local hydraulic interpretation was
completed in the same pass. If the manuscript needs those claims, they should
come from a later phase-2 package rather than from softened language here.

## Recommended paper structure using this package

A pragmatic drafting sequence is:

1. Methods:
   describe the monitor-first postprocessing workflow using
   `reports/methodology.md`.
2. Dataset and maturity:
   summarize the 13-run inventory, runtime states, and readiness labels using
   `data/run_index.csv` and `data/readiness_matrix.csv`.
3. Family-level validation context:
   compare water and salt-family wall-temperature / external-loss behavior using
   `data/cross_run_summary.csv` plus the June 9 heat audit.
4. Representative case interpretation:
   cite per-run report packages for one water row, one Salt Jin row, one Salt
   Kirst row, and the live Salt 2 continuation.
5. Limitations and future work:
   keep the explicit pressure, continuation-time-base, and reconstruction
   boundaries from `TODO.md` and the workflow journal.

## Suggested representative figures and tables

Good manuscript candidates from the canonical campaign package:

- readiness / runtime summary table from `data/readiness_matrix.csv`
- family-level validation summary table from `data/cross_run_summary.csv`
- wall-temperature RMSE by run from `data/comparison_tw_rmse_by_run.csv`
- ambient-loss proxy comparison from `data/heat_transfer_ambient_proxy_by_run.csv`
- runtime final time by run from `data/runtime_final_time_by_run.csv`

For any representative per-run figure, prefer citing the corresponding
`runs/<source_id>/reports/artifact_map.md` so the manuscript points to the exact
CSV and rendered assets used.

## Not yet supported as strong paper claims

Avoid these claim forms unless a later package adds new evidence:

- “The salt family is converged and validated.”
- “Kirst-property cases resolve the validation gap.”
- “The base Salt 2 case matches experiment at the current continuation tail.”
- “Pressure behavior confirms the hydraulic interpretation.”
- “Field slices in this campaign prove the local mechanism of the salt-family
  heat-loss discrepancy.”

## Handoff summary

The Ethan postprocessing queue wave is closed and review-clean. The resulting
campaign is ready to serve as a manuscript backbone for monitor-derived
comparison and evidence-linked drafting, provided the paper keeps three
boundaries explicit:

- workflow maturity is not the same thing as validation quality
- the live Salt 2 continuation is time-base mixed
- pressure and richer field reconstruction remain future-work layers

If a paper needs stronger hydraulic, pressure, or local heat-loss mechanism
claims, open a follow-on phase-2 package rather than stretching this v1
campaign beyond the evidence it actually contains.
