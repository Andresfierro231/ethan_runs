# AGENT-086 Raw Journal — Salt Conclusions and Water Phase 1

## 2026-06-18

- Re-read the repo startup instructions, board, file ownership map, role map,
  and `tools/AGENTS.override.md` before claiming the new continuation scope.
- Opened `AGENT-086` because the previous Salt hardening work had produced
  enough technical evidence to justify:
  - a final Salt conclusions layer
  - a bounded Water phase-1 readiness package
- Chose not to edit any shared extractor files. This task stays entirely
  additive and report-coupled.

### Salt conclusions package

- Built `tools/analyze/build_ethan_salt_conclusions_package.py`.
- Purpose:
  - translate the v2 Salt dependency package into a scientist-facing handoff
  - make the defended/provisional/refused boundary explicit
  - keep exact admitted rows, exclusion summaries, and blocked-method
    requirements machine-readable
- Inputs:
  - `reports/2026-06-19_ethan_salt_model_dependency_package_v2/**`
- Outputs chosen:
  - `dependency_status.csv`
  - `exact_fit_used_rows.csv`
  - `case_contribution_summary.csv`
  - `exclusion_reason_rollup.csv`
  - `sensitivity_interpretation.csv`
  - `blocked_dependency_requirements.csv`
  - `salt_dependency_conclusions.md`
  - `upstream_requirements.md`
- Main intent:
  - avoid making another technical package that still requires the reader to
    infer the final scientific posture from JSON
  - make the caveat boundary obvious:
    - straight-section friction is usable with explicit caveats
    - feature `K_eff` is usable with explicit caveats
    - Salt Nu is still blocked

### Water phase-1 starter package

- Built `tools/analyze/build_ethan_water_phase1_starter_package.py`.
- Reconnaissance before implementation:
  - the existing Water hydraulic evidence subset already provides the cleanest
    current Water-family branch-pressure candidates
  - the June 17 pressure/HTC package already contains:
    - exact water bulk reweighting summary
    - section-level pressure closure
    - section-level HTC/Nu fields
    - leg-level enthalpy rows
- Chose a conservative scope:
  - do not claim any defended Water dependency
  - do identify where a real water closure program should start
- Implemented Water outputs:
  - `water_case_context.csv`
  - `water_hydraulic_branch_readiness.csv`
  - `water_thermal_span_phase1.csv`
  - `water_bulk_reweight_context.csv`
  - `water_dependency_readiness.csv`
  - `water_phase1_handoff.md`
- Important water classifications observed:
  - hydraulic candidates:
    - `right_leg`
    - `test_section_span`
    - `upper_leg`
  - hydraulic contextual only:
    - `left_upper_leg`
    - `lower_leg`
  - hydraulic excluded:
    - `left_lower_leg`
  - thermal closure-rebuild candidate:
    - `left_upper_leg`
  - thermal closure-rebuild priority:
    - `test_section_span`
- Key interpretation:
  - Water `test_section_span` has the strongest thermal support but still poor
    enthalpy-vs-wall sign consistency, so it is a closure-rebuild priority, not
    a dependency-ready thermal span
  - Water `left_upper_leg` has the clearest “support exists, closure moderate”
    profile for the next thermal hardening pass

### Tests and validation

- Added `tools/analyze/test_ethan_salt_conclusions_and_water_phase1.py`.
- Test coverage kept narrow and decision-relevant:
  - Salt conclusions use-label mapping
  - Salt sensitivity robustness classification
  - Water thermal phase-1 branch classification:
    - hydraulic exclusion
    - closure-rebuild priority
    - closure-rebuild candidate
- Validation path:
  - `python -m py_compile ...`
  - `python -m unittest discover -s tools/analyze -p 'test_ethan_salt_conclusions_and_water_phase1.py'`
  - bounded Salt conclusions smoke build
  - bounded Water starter smoke build
  - durable Salt conclusions build
  - durable Water starter build
  - final schema/sanity audit:
    - Salt thermal status still blocked
    - Water hydraulic candidate count is `3`
    - Water thermal starter identifies `left_upper_leg` and `test_section_span`
      in the intended categories

### Final scientific posture from this task

- Salt:
  - a clearer conclusions layer now exists
  - the repo now contains an explicit list of what can be used, what cannot,
    and what upstream method changes would move the boundary
- Water:
  - the first few rigorous steps are now implemented
  - the next actual water execution work should begin from:
    - hydraulic: `right_leg`, `test_section_span`, `upper_leg`
    - thermal: `left_upper_leg` and `test_section_span`
- Nothing in this task promotes Water to defended dependency status.
