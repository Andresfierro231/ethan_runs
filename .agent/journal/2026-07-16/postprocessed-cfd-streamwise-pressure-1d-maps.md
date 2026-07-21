---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv
  - work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/station_pressure_ladder.csv
  - work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/case_provenance_manifest.csv
  - work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/README.md
tags: [pressure-ladder, cfd-postprocessing, streamwise-pressure, provenance]
related:
  - .agent/status/2026-07-16_AGENT-457.md
  - imports/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps.json
task: AGENT-457
date: 2026-07-16
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Postprocessed CFD Streamwise Pressure / 1D Maps

## Observed Output

The reusable builder integrated the two available station-pressure ladder
harvests:

| Harvest | Job | Station rows | Cases |
|---|---:|---:|---|
| AGENT-445 pressure ladder unlock | `3297860` | `90` | `salt2_mainline`, `salt3_mainline`, `salt4_mainline` |
| AGENT-447 expanded pressure ladder | `3297863` | `240` | `salt1_nominal`, `salt1_lo10q`, `salt1_hi10q`, `salt2_lo5q`, `salt2_hi5q`, `salt4_lo5q`, `salt4_hi5q`, `val_salt2` |

The final package contains `330` station rows and `66` branch-average rows
across `11` case keys.

## Provenance

The authoritative provenance table is
`work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/case_provenance_manifest.csv`.
It records, per case:

- `case_key`, `case_id`, `split_role`, and postprocessed `time_s`
- native source case path from the harvest source manifest
- harvest package, task, job ID, station CSV, and summary JSON
- source station row count and mapped station row count
- admission caveat, fit eligibility, and blockers

The package also writes one per-case Markdown file under `per_case/` with the
source case path, job ID, station CSV, source ID, split role, window, and branch
average pressure table.

## Interpretation

The mapping intentionally uses mesh/span labels, not schematic probe labels:

- `lower_leg` is the heater/bottom heated incline and maps to Fluid
  `heated_incline`; it is traversed `s04 -> s00`.
- `right_leg` is the downcomer and maps to Fluid `right_vertical`; it is
  traversed `s00 -> s04`.
- `upper_leg` is the cooled top path and maps to the Fluid top/HX composite.
- `left_lower_leg`, `test_section_span`, and `left_upper_leg` map to the
  upcomer/test-section path.

Use `mean_p_Pa` for static pressure values. Preserve `mean_p_rgh_Pa` as the
OpenFOAM gravity-adjusted pressure diagnostic. These rows remain diagnostic
pressure-map evidence, not admitted distributed `f_D` or component-`K`
coefficients.

## Reusable Script

Yes. The reusable script is
`tools/analyze/build_postprocessed_streamwise_pressure_1d_maps.py`, with tests in
`tools/analyze/test_postprocessed_streamwise_pressure_1d_maps.py`. It reads the
source manifests and station ladders, validates 30 stations per case, applies
the same branch orientation and 1D mapping to each case, and regenerates the
aggregate plus per-case documentation.

## Validation

- `python3.11 -m unittest tools.analyze.test_postprocessed_streamwise_pressure_1d_maps` passed `5/5`.
- `python3.11 tools/analyze/build_postprocessed_streamwise_pressure_1d_maps.py` regenerated the package.
- `python3.11 -m json.tool imports/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps.json` parsed successfully.
- `python3.11 -m json.tool work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/summary.json` parsed successfully.

Generated docs index refresh was intentionally skipped because generated index
files were outside this task's claimed scope.
