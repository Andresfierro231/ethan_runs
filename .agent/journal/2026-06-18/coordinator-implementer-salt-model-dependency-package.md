# AGENT-084 Raw Journal — Salt Model Dependency Package

## 2026-06-18

- Re-read the repo startup instructions, board, file-ownership map, role map,
  and `tools/` local override before touching a new analysis layer.
- Opened `AGENT-084` as a new additive task because the user asked for a
  defensible model-dependency package, not another dashboard.
- Decided the package must stay downstream of the existing June 15/17/18
  additive artifacts unless a hard code/data dependency forced upstream work.
- Reconnaissance pass:
  - mapped the June 18 checkpoint suite phase outputs back to their builders
  - mapped the June 18 Salt closure/correlation tables to the June 17 pressure /
    HTC / boundary-layer package and the June 15 field-transport campaign
  - confirmed the critical gaps:
    - feature `K_eff` is still residual `p_rgh` only
    - thermal closure is mainly limited by enthalpy-vs-wall-heat mismatch
    - `right_leg` must remain hard-blocked
    - `upcomer` is derived/overlapping and should not enter defended fitting
- Chose the new package shape:
  - `tools/analyze/build_ethan_salt_model_dependency_package.py`
  - `tools/analyze/test_ethan_salt_model_dependency_package.py`
  - `reports/2026-06-18_ethan_salt_model_dependency_package/`
- Chose to implement thermal decomposition first because the preserved artifacts
  were sufficient to build a bounded, explicit heat/enthalpy closure pass
  without inventing new extractor results.
- Kept hydraulic hardening in scope as an explicit audit because the user
  required it, but did not fake a new feature pressure-loss method when the
  additive inputs lacked the needed hydro-integral/path data.
- Implemented the builder to:
  - validate required input columns before use
  - centralize thresholds and formulas rather than scattering magic constants
  - compute Salt properties from each case `case_config.yaml` using the stored
    polynomial / `expInvT` models
  - derive branch-level thermal decomposition rows with explicit intended,
    parasitic, grouped-reconstruction, and residual buckets
  - preserve bulk-vs-centerline correction as an explicit reported term
  - enforce the thermal gate stack:
    - connected-flow support
    - `|T_wall - T_bulk|` support strength
    - enthalpy-vs-wall residual fraction
    - thermal direction consistency
    - hard block for `right_leg`
    - sensitivity-only handling for derived `upcomer`
  - build a hydraulic hardening audit that distinguishes:
    - defended direct hydro straight-section rows
    - residual-only feature rows
    - buoyancy-aided/net-gain straight sections
    - direct-to-shear disagreement exclusions
  - fit only what the gates support:
    - straight-section Salt friction
    - screened exploratory Salt thermal dependency
  - write a provenance map for outputs, formulas, units, sign conventions,
    validity gates, and known failure modes
  - write a model-builder handoff instead of leaving interpretation buried in
    JSON or code
- Implemented the unit-test file to cover:
  - property evaluators
  - residual normalization
  - sign handling
  - `right_leg` policy exclusion
  - derived-branch sensitivity-only handling
  - weak thermal support exclusion
  - loose enthalpy closure exclusion
  - direction-consistency exclusion
  - nonpositive residual feature exclusion
  - buoyancy-aided hydraulic exclusion
  - hydraulic candidate promotion
  - output schema expectations
- Validation sequence:
  - `python -m py_compile tools/analyze/build_ethan_salt_model_dependency_package.py tools/analyze/test_ethan_salt_model_dependency_package.py`
  - `python -m unittest discover -s tools/analyze -p 'test_ethan_salt_model_dependency_package.py'`
  - smoke build on:
    - `val_salt_test_2_coarse_mesh_laminar`
    - `viscosity_screening_salt_test_4_jin_coarse_mesh`
  - full durable build on all `9` Salt cases
- During validation, found that the first property-convention sensitivity was
  not actually comparing the same screened direct-branch subset. Fixed that by:
  - building a distinct `case_probe` thermal-row table
  - restricting that sensitivity to the same screened direct-branch family
  - adding a second thermal sensitivity that swaps the target to the preserved
    latest section-summary values
- Ran a post-build schema/sanity audit to confirm:
  - no `right_leg` rows survived into `thermal_fit_ready_rows.csv`
  - no feature rows survived into `fit_used`
  - all fit-used hydraulic rows have positive pressure loss and positive
    apparent Darcy friction factor
  - summary counts reconcile with table counts
- Main final outcomes:
  - friction:
    - `12` defended straight-section rows survive
    - only `lower_leg` and `test_section_span` remain fit-used
    - the preferred model is a class-aware `f ~ Re^b` power law
    - status remains `provisional_defended` because unfinished feature closure
      still limits the full loop resistance story
  - thermal:
    - `36` rows survive initial branch screening
    - only `1` row survives full closure support
    - therefore the Salt Nu dependency remains `not_defensible_yet`
    - an exploratory screened-only branch-aware `Nu ~ Re^b` model is still
      reported for sensitivity context, but not recommended for downstream use
- Sensitivity outcomes preserved explicitly:
  - hydraulic direct/shear strictness changes retained rows and nudges the slope
    slightly, so the friction dependency is only provisional
  - thermal property convention (`branch bulk` vs `case probe`) does not change
    the qualitative screened-only story
  - thermal late-window target choice changes the exploratory slope noticeably,
    which reinforces the decision not to promote a defended Nu dependency yet
  - hydraulic late-window sensitivity could not be run because the preserved
    additive artifacts do not include the needed time-resolved hydro-corrected
    closures
- No repo-level formatter/linter config was found while searching for
  `pyproject.toml`, `setup.cfg`, `pytest.ini`, `.ruff.toml`, and `tox.ini`, so
  no extra formatting command was available beyond keeping the code and outputs
  mechanically consistent.
- Final package size and content are suitable for handoff:
  - one self-contained report root
  - one provenance map
  - one model-builder handoff
  - one test file that locks the main gate logic in place
