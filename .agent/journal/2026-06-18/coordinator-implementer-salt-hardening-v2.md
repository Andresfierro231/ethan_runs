# AGENT-085 Raw Journal — Salt Hardening v2

## 2026-06-18

- Re-read the repo startup instructions, board, file ownership, role map, and
  `tools/AGENTS.override.md` before starting the next continuation task.
- Opened `AGENT-085` because the requested continuation work touched new report
  roots and new analyzer code, but could not legally modify the shared
  extraction files currently owned by `AGENT-072`.
- Reconnaissance pass:
  - confirmed the shared extractor files needed for a true upstream rebuild are
    owned elsewhere
  - mapped the June 18 checkpoint suite and June 18 dependency package back to
    the raw preserved June 15 live case-analysis roots
  - verified the preserved raw tables were sufficient to do the next hardening
    pass additively:
    - `feature_minor_loss_timeseries.csv`
    - `major_loss_cumulative_timeseries.csv`
    - `major_loss_summary.csv`
    - `azimuthal_wall_transport_summary.csv`
    - June 17 retained-time enthalpy / HTC / bulk-centerline tables
- Decided the only compliant path was:
  - no edits to the shared extractors
  - new additive analyzers in `tools/analyze/`
  - new dated report packages under `reports/2026-06-19_*`

### Shared helper layer

- Added `tools/analyze/ethan_salt_hardening_common.py` to centralize:
  - case-context loading from the Salt dashboard and case metadata index
  - fluid-property evaluation from each case `case_config.yaml`
  - dimensionless bundle construction
  - local boundary-bin support extraction
  - normalized residual and sign-token helpers
  - explicit CSV write helper with schema support for empty fit-ready tables
- Chose to keep all thresholds and shared physical conventions in code rather
  than scattering magic values across three builders.

### Feature hydraulic hardening

- Built `tools/analyze/build_ethan_salt_feature_hydraulic_hardening.py`.
- Method choice:
  - use the preserved patch-endpoint `p_rgh` feature deltas as the observed
    local feature pressure-loss magnitude
  - rebuild the adjacent straight reference from the nearest finite major-span
    boundary bins on both feature sides
  - compute a local excess feature loss and local effective `K_eff`
- Important modeling decision:
  - this is stronger than the June 18 residual-only feature budget, but it is
    still not a full feature-path hydro integral
  - I documented that limitation explicitly in the package README and math note
- First smoke build showed:
  - `corner_upper_right` and `test_section_complex` survive cleanly
  - lower corners remain nonpositive
  - this matched the earlier exploratory scan
- Found a downstream issue later: the case-level feature table was not carrying
  `mean_keff_effective_local`, which caused the v2 dependency builder to see
  `NaN` feature targets. Patched the feature builder and reran it.

### Thermal closure hardening

- Built `tools/analyze/build_ethan_salt_thermal_closure_hardening.py`.
- Method choice:
  - reconstruct exact retained-time branch rows from:
    - June 17 enthalpy balance by leg
    - June 17 section-integral wall heat / HTC / Nu
    - June 17 bulk-vs-centerline correction
    - preserved June 15 azimuthal wall transport
    - preserved June 15 major-span support rows
  - keep separate buckets for:
    - `Q_enthalpy`
    - `Q_wall_total`
    - `Q_intended_transfer`
    - `Q_external_or_loss`
    - `Q_sink_or_cooling`
    - `Q_junction_or_unresolved`
    - `Q_bulk_centerline_correction_proxy`
    - `Q_residual`
- Gate policy enforced:
  - `right_leg` hard-blocked
  - `upcomer` sensitivity-only because it is a derived/overlapping branch
  - support fraction, `|Twall-Tbulk|`, residual fraction, grouped
    reconstruction, and enthalpy/wall direction all must pass
- Efficiency fix:
  - cached grouped wall-heat and support tables once per case instead of
    recomputing them inside every branch loop
- Important result:
  - the full 9-case package still only produces `2` defended thermal rows, both
    on `left_lower_leg` and both from Kirst Salt continuation cases
  - this means the package successfully documents the closure, but still refuses
    to promote Salt Nu to defended status

### v2 dependency package

- Built `tools/analyze/build_ethan_salt_model_dependency_package_v2.py`.
- Combined:
  - defended straight-section rows from the June 18 dependency package
  - new feature hardening case rows
  - new thermal hardening case rows
- Added:
  - aggregated exclusion summaries
  - sensitivity suite for:
    - strict vs loose direct/shear hydraulic gates
    - feature boundary-bin count
    - thermal closure threshold
    - property convention
    - latest-time-only thermal target
    - explicit `not_run` hydraulic late-window note
  - water extension TODO in the final report root
- Sequencing mistake caught during validation:
  - I initially relaunched the durable feature rebuild and durable v2 rebuild in
    parallel
  - that allowed v2 to read the stale pre-patch feature table and preserve
    `NaN` feature targets
  - verified the feature normalization independently, then reran the v2 build
    after the corrected feature build completed

### Testing and validation

- Added `tools/analyze/test_ethan_salt_hardening_v2.py`.
- Test coverage locks:
  - residual normalization
  - local boundary support extraction
  - nonpositive feature-loss exclusion
  - feature stability thresholding
  - `right_leg` hard exclusion
  - weak thermal support exclusion
  - derived `upcomer` sensitivity-only behavior
  - direct thermal fit-row filtering
  - feature normalization fallback
  - exclusion-summary aggregation
- Validation sequence used:
  - `python -m py_compile ...`
  - `python -m unittest discover -s tools/analyze -p 'test_ethan_salt_hardening_v2.py'`
  - smoke feature package on Salt 2 val + Salt 4 Jin
  - smoke thermal package on Salt 2 val + Salt 4 Jin
  - smoke v2 package using explicit `--feature-dir` and `--thermal-dir`
  - durable feature package
  - durable thermal package
  - durable v2 package
  - explicit schema/sanity audit over the final v2 outputs
- Environment-specific notes:
  - direct script execution failed because `tools` was not importable unless the
    repo root was on `PYTHONPATH`; switched all build commands to `python -m`
  - `python3.11` lacked `numpy`; all builds stayed on `python`

### Final outcomes

- Feature hydraulic hardening:
  - `45` feature case rows
  - `21` fit-ready feature rows
  - stable defended feature families in v2:
    - `corner_upper_right`
    - `test_section_complex`
  - `corner_upper_left` improved but remains below the stability threshold
- Thermal closure hardening:
  - `63` branch case rows
  - `2` defended thermal rows
  - both defended rows are `left_lower_leg`
- v2 dependency package:
  - straight-section friction stays `provisional_defended`
  - feature `K_eff` moves from the old refusal state to `provisional_defended`
    under the documented local-boundary-reference method
  - Salt HTC/Nu remains `not_defensible_yet`
- Main exclusions remain physically and methodologically interpretable:
  - hydraulic:
    - buoyancy-aided/net-gain sections
    - direct-vs-shear disagreement
    - nonpositive local feature excess
  - thermal:
    - enthalpy-vs-wall closure looseness
    - support-marginal branches
    - `right_leg` policy block
    - derived `upcomer` overlap

### Remaining scientific blockers

- The feature path is still not a full hydro-integral closure. It is now
  defendable enough for a provisional `K_eff` model, but not yet immune to the
  choice of local straight-reference construction.
- The Salt thermal side still lacks enough direct closure-supported rows for a
  defended Nu dependency.
- Hydraulic late-window sensitivity is still unavailable because the preserved
  additive straight-section rows are case-level means rather than retained-time
  defended closures.
