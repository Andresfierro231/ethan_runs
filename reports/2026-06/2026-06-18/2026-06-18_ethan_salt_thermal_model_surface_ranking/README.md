# Salt Thermal Model Surface Ranking

Generated: `2026-06-18T16:14:17-05:00`

## Purpose

Rank the already-defended Salt thermal modeling surfaces on the existing safe branch subset only. This package does not reopen extraction, branch trust gates, or cross-family promotion.

## Inputs

- `reports/2026-06-18_ethan_transport_interpretation_closure/branch_thermal_interpretation.csv`
- Salt branch summaries under the preserved June 15 package roots:
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/*/branch_thermal_summary.csv`
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/*/branch_thermal_summary.csv`

## Safe Salt branch subset

- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upcomer`

## Decision

- Primary Salt thermal modeling surface: `Effective UA'(x)`
- Secondary Salt thermal modeling surface: `Effective HTC(x)`
- Keep `branch-averaged R'_th` as supporting-only.
- Keep `R'_th(x)` as diagnostic-only.

## Why

- All four branches remain scrutiny-cleared in the June 18 interpretation closure.
- Minimum usable fraction across the safe subset stays above `0.94`.
- Maximum branch warning fraction across the safe subset stays below `0.06`.
- Minimum resolved `|T_bulk - T_wall|` across the safe subset stays above `2.03 K`, well above the current `0.50 K` floor.
- `UA'` and `HTC` have comparable case-to-case stability, but `UA'` avoids the extra wall-area normalization embedded in HTC.
- `R'_th` is materially more fragile because the reciprocal transform amplifies the same low-conductance regions that already challenge UA'.

## Branch stability summary

| Branch | Min usable fraction | Max warning fraction | Min |T_bulk-T_wall| [K] | HTC rel-CV | UA' rel-CV | R'_th rel-CV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| left_lower_leg | 0.941 | 0.059 | 2.032 | 0.343 | 0.343 | 0.313 |
| test_section_span | 1.000 | 0.000 | 2.166 | 0.457 | 0.460 | 0.931 |
| left_upper_leg | 0.949 | 0.051 | 2.032 | 0.210 | 0.209 | 0.233 |
| upcomer | 0.960 | 0.040 | 2.032 | 0.328 | 0.326 | 0.476 |


## Source paths

- `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_jin_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_kirst_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_3_jin_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_3_kirst_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_4_jin_coarse_mesh/branch_thermal_summary.csv`
- `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_4_kirst_coarse_mesh/branch_thermal_summary.csv`

## Reproduction

```bash
python tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py \
  --output-dir reports/2026-06-18_ethan_salt_thermal_model_surface_ranking
```
