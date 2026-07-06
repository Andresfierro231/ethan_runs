# AGENT-080 Raw Journal — Salt Closure / Correlation Package

## 2026-06-18

- Re-read the repo startup instructions, task board, file-ownership map, and
  `tools/` local override before editing.
- Opened a new additive Salt-only task instead of touching the active June
  15/17 shared extraction and package-builder paths owned by `AGENT-072` and
  the existing additive June 17 pressure package owned by `AGENT-079`.
- Decided the implementation should be one fresh builder plus one fresh report
  package:
  - `tools/analyze/build_ethan_salt_closure_correlation_package.py`
  - `reports/2026-06-18_ethan_salt_closure_correlation_package/`
- Grounded the package in existing artifact families rather than new
  extraction:
  - June 17 additive pressure / HTC / boundary-layer package
  - June 17 Salt/water nondimensional dashboard
  - June 15 all-runs branch-thermal campaign
  - June 9 steady-state heat-flow audit
- Confirmed the current reusable schemas before coding:
  - sectionwise pressure closure columns
  - feature `K_eff` columns
  - legwise enthalpy-balance columns
  - branch-thermal comparison columns
  - boundary-layer summary/profile columns
  - heat-audit latest and late-window columns
- Chose to keep the package closure-first and Salt-only, with these outputs:
  - Salt hydraulic section screening
  - Salt hydraulic case summary
  - Salt feature `K_eff` screening
  - Salt heat-loss partition indicators
  - Salt legwise enthalpy summary
  - Salt branch thermal usability mask
  - Salt boundary-layer context
  - Salt case / straight-section / feature correlation-input tables
  - one fit-exclusion log
- Implemented the Salt builder to:
  - reuse the additive June 17 signed apparent Darcy closures
  - classify straight sections as `candidate`, `screening_only`, or
    `do_not_fit`
  - classify branches with the June 17 scrutiny thresholds
  - classify feature `K_eff` rows by sign and residual usefulness
  - summarize legwise enthalpy residual fractions as a closure screen
  - build case-level heat-loss indicators from the June 9 audit
  - publish Salt-only correlation-input tables for cases, straight sections,
    and features
  - render reusable Salt-only figures in PNG/SVG/PDF
  - write a README, math companion, and summary JSON
- First smoke run failed because the smoke subset narrowed the dashboard rows
  but not the upstream pressure/heat/branch inputs. Fixed by adding a central
  source-ID filter pass before any joins.
- Smoke build then completed for:
  - `val_salt_test_2_coarse_mesh_laminar`
  - `viscosity_screening_salt_test_4_jin_coarse_mesh`
- Promoted the same builder to the full durable package covering all `9`
  Salt-family cases.
- Final durable package summary counts:
  - `case_count = 9`
  - `straight_section_row_count = 54`
  - `feature_row_count = 45`
  - `branch_row_count = 63`
  - `enthalpy_row_count = 54`
  - `boundary_summary_row_count = 54`
  - `representative_profile_row_count = 7015`
  - `straight_section_fit_candidates = 12`
  - `feature_fit_candidates = 19`
  - `branch_fit_candidates = 36`
  - `enthalpy_fit_candidates = 1`
- Final durable package size:
  - `4.3M`
- Important observed results preserved for follow-on work:
  - every Salt case still has exactly two buoyancy-aided or net-gain straight
    sections under the signed hydro-corrected section closure
  - the current direct/shear disagreement keeps several `upper_leg` rows in
    `screening_only`
  - branch usability is strong for `left_lower_leg`, `left_upper_leg`,
    `test_section_span`, and `upcomer`, but `right_leg` and several
    `lower_leg`/`upper_leg` rows remain blocked or marginal
  - enthalpy closure is currently much weaker than the branch thermal support;
    only one Salt span passes the current candidate threshold
- Important limitations kept explicit in the package:
  - feature `K_eff` still inherits the residual `p_rgh` feature path
  - heat-loss partition is still case-level and audit-style, not a resolved
    thermal-resistance decomposition
  - representative boundary-layer context is currently limited to the
    preserved Salt 2 landmark profile set
