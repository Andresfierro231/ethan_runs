# 2026-06-18 Ethan Runs

## Summary

Today’s work turned the existing package/campaign/scrutiny stack into a paper-ready staging workflow without editing the paper repo itself. The main result is two new report packages:

- `reports/2026-06-18_ethan_transport_analysis_package`
- `reports/2026-06-18_ethan_salt_paper_handoff_package`

The first is the all-runs interpretation and staging audit. The second is the Salt-only manuscript handoff that maps staged figures and tables into the current `3d_analysis` section structure.

## Observed Output

- The June 17 scrutiny gate remained the right starting point:
  - Salt branch-thermal promotion still narrowed to `left_lower_leg`, `test_section_span`, `left_upper_leg`, and `upcomer`.
  - The two `requires_code_fix = yes` hydraulic contradiction rows remained:
    - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
    - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- The new all-runs analysis package reports:
  - `3` grouped `established_result` rows
  - `27` grouped `salt_only_result` rows
  - `6` grouped `water_only_result` rows
  - `135` grouped `family_only_result` rows
  - `11` grouped `support_limited` rows
  - `258` grouped `contradictory` rows
- The new Salt-paper handoff package stages `12` Salt assets:
  - `8` main-text or candidate-main-text assets
  - `2` appendix-support figures
  - `2` table candidates

## Inferred Interpretation

- The Salt paper can move forward without reopening extraction or re-deciding the safe subset.
- The family-level Salt story remains:
  - heat-loss redistribution
  - circumferential-mean azimuthal redistribution
  - branch-local effective thermal redistribution only on the scrutiny-cleared branches
- The matched Salt 2 mechanism story can now be staged with:
  - hydraulic mechanism figure
  - effective-thermal mechanism figure
  - branch-thermal safe-subset figure
- Cross-family all-runs results are now interpreted and staged for internal screening, but they are still intentionally blocked from the Salt manuscript surface.

## Contradictions And Limits

- The two Water `left_lower_leg` hydraulic rows remain the only `priority_rank = 1` contradiction items in the new analysis package.
- Salt 2 boundary-layer figures remain blocked from headline use.
- The Salt 2 hydraulic mechanism figure is still usable only with the caveat that claims stay at the broad redistribution level, not at every local direct-vs-shear fluctuation.
- Branch-thermal promotion still excludes weaker-support branches such as the right leg and lower leg from manuscript headline use.

## Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_transport_analysis_package.py`
  - `tools/analyze/build_ethan_salt_paper_handoff_package.py`
- Validation path:
  - `py_compile` on both builders
  - smoke build to `tmp/2026-06-18_*`
  - durable build to `reports/2026-06-18_*`
- One compatibility issue surfaced during the handoff smoke build:
  - `zip(..., strict=True)` is not supported on this runtime
  - fixed by removing `strict=True`
- One path-layout bug surfaced:
  - report figure bundles live at `figures/<fmt>/<stem>.<fmt>`
  - fixed the handoff builder to copy full format bundles from that structure

## Next Suggested Actions

- Open a dedicated `../papers` task before touching `3d_analysis`.
- Use only the Salt handoff package as the manuscript promotion surface:
  - `staged_assets_manifest.csv`
  - `figure_claim_map.csv`
  - `table_claim_map.csv`
- Keep the two Water `left_lower_leg` hydraulic contradictions on the follow-up queue before making stronger cross-family hydraulic claims in any later paper or report.

## Focused Scientific Interpretation Package

Later the same day, the broad all-runs analysis package was tightened into one
focused scientific interpretation package:

- `reports/2026-06-18_ethan_transport_scientific_interpretation_package`

This was intentionally not another extraction or dashboard layer. It was a
skeptical interpretation pass over the already-built packages.

### Observed Output

- The package examined exactly the two priority-one hydraulic contradiction rows:
  - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
  - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- It produced:
  - `contradiction_resolution_rows.csv`
  - `branch_thermal_interpretation.csv`
  - `scientific_conclusions.csv`
  - `internal_only_decisions.csv`
  - `cross_family_claims_audit.csv`
  - `methods_interpretation.md`
  - `model_dependency_readiness.md`
  - `remaining_blockers.md`

### Inferred Interpretation

- Water 1 `left_lower_leg` is now best treated as a resolved exclusion:
  - the branch-end cumulative direct `p_rgh` drop stays positive
  - the mean direct gradient changes sign only because mixed-sign local direct
    bins nearly cancel on a weak signal
- Water 2 `left_lower_leg` remains unresolved for use:
  - the direct `p_rgh` signal is weak
  - one retained time carries mixed `flow_alignment_sign`
  - the branch mean is therefore not mechanically traceable to one stable sign
    convention
- Salt-only effective thermal dependency construction is now explicitly bounded
  to the safe subset:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- Water left-side effective thermal dependency construction remains blocked by
  small `|T_bulk - T_wall|` and weak support.

### Contradictions And Limits

- Cross-family hydraulic claims remain blocked.
- Momentum resistance remains a proxy, not a direct closure-quality quantity.
- Boundary-layer landmarks remain contextual-only.
- Salt `right_leg` thermal behavior remains internal-only rather than
  headline-safe.

### Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_transport_scientific_interpretation_package.py`
- Validation:
  - `python -m py_compile tools/analyze/build_ethan_transport_scientific_interpretation_package.py`
  - `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir tmp/2026-06-18_ethan_transport_scientific_interpretation_package_smoke`
  - `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir reports/2026-06-18_ethan_transport_scientific_interpretation_package`

## Transport Interpretation Closure

Later the same day, the focused interpretation package was tightened one more
time into a closure package:

- `reports/2026-06-18_ethan_transport_interpretation_closure`

This was not a new extraction wave. It was one bounded forensic audit of
Water 2 `left_lower_leg`.

### Observed Output

- The closure package added:
  - `water2_left_lower_leg_hydraulic_audit.csv`
  - `water2_left_lower_leg_hydraulic_audit.md`
  - revised contradiction, conclusions, claims-audit, methods, readiness, and
    blockers outputs
- It changed Water 2 `left_lower_leg` from:
  - `unresolved_exclude`
  to:
  - `resolved_exclude`

### Inferred Interpretation

- Water 2 `left_lower_leg` is still not usable hydraulic evidence.
- The difference is that the branch is now excluded because the retained-time
  audit shows:
  - positive branch-end cumulative direct `p_rgh` drop in every retained time
  - one unique non-modal alignment-sign window
  - the remaining mean-sign changes are weak-signal local cancellation
    artifacts rather than stable branchwise reversal
- Cross-family hydraulic work stays blocked, but now because the Water
  `left_lower_leg` evidence subset is excluded rather than because a sign
  mystery remains unresolved.

### Contradictions And Limits

- Water 1 `left_lower_leg`: resolved exclusion
- Water 2 `left_lower_leg`: resolved exclusion
- Salt safe thermal subset unchanged:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- `right_leg` thermal remains blocked from headline use.
- Boundary-layer landmarks remain contextual-only.

### Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_transport_interpretation_closure.py`
- Validation:
  - `python -m py_compile tools/analyze/build_ethan_transport_interpretation_closure.py`
  - `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir tmp/2026-06-18_ethan_transport_interpretation_closure_smoke`
  - `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir reports/2026-06-18_ethan_transport_interpretation_closure`

## Water Hydraulic Evidence Subset

After the closure pass, the next science-facing step was to move future
Water-family hydraulic interpretation off the excluded `left_lower_leg` branch
and onto an explicit bounded subset:

- `reports/2026-06-18_ethan_water_hydraulic_evidence_subset`

### Observed Output

- The package screened all four Water case packages branch-by-branch using:
  - per-case `major_loss_summary.csv`
  - per-case `major_loss_cumulative_timeseries.csv`
  - the June 18 interpretation closure package
- It published:
  - `water_hydraulic_case_branch_screen.csv`
  - `water_hydraulic_family_subset.csv`
  - `water_hydraulic_cross_family_guardrails.csv`

### Inferred Interpretation

- Water-family hydraulic candidate branches:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`
- Water-family contextual-only branches:
  - `lower_leg`
  - `left_upper_leg`
- Water-family excluded branch:
  - `left_lower_leg`

### Contradictions And Limits

- `lower_leg` stayed contextual-only because Water 4 carries one weak-signal
  retained-time direct sign failure.
- `left_upper_leg` stayed contextual-only because Water 2 carries one retained
  time with non-positive cumulative direct branch-end `p_rgh` drop.
- No branch in this package was promoted directly to cross-family hydraulic
  readiness.

### Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`
- Validation:
  - `python -m py_compile tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`
  - `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_water_hydraulic_evidence_subset_smoke`
  - `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_water_hydraulic_evidence_subset`

## Salt Hydraulic Evidence Subset And Closure-Aware Paper Handoff Refresh

The next paired move was to do both the analogous Salt-family hydraulic
screen and the paper-facing closure refresh without touching `../papers`.

### Observed Output

- New Salt-family hydraulic subset package:
  - `reports/2026-06-18_ethan_salt_hydraulic_evidence_subset`
- Refreshed Salt-only paper handoff package:
  - `reports/2026-06-18_ethan_salt_paper_handoff_package`
- The Salt subset package published:
  - `salt_hydraulic_case_branch_screen.csv`
  - `salt_hydraulic_family_subset.csv`
  - `salt_hydraulic_overlap_with_water.csv`
- The refreshed handoff package added:
  - `closure_gate_note.md`
  - updated `README.md`
  - updated `summary.json`

### Inferred Interpretation

- All six Salt branches are clean at the current family-only hydraulic screen:
  - `lower_leg`
  - `right_leg`
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upper_leg`
- The current shared clean Salt/Water overlap is narrower:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`
- That overlap is still not cross-family-ready. The closure package still
  blocks cross-family hydraulics because the Water `left_lower_leg` evidence is
  excluded and the broader branch overlap has not been promoted beyond guarded
  family-specific use.
- The Salt paper handoff remains valid. The important change is provenance and
  claim gating, not the staged figure set itself.

### Contradictions And Limits

- `left_lower_leg` remains Salt-only clean but Water-excluded.
- `lower_leg` and `left_upper_leg` remain Salt-only clean but Water-contextual.
- No new branch was promoted directly into cross-family hydraulic fitting.
- The paper-facing handoff still requires a separate `../papers` task before
  any manuscript edits happen.

### Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py`
- Refreshed:
  - `tools/analyze/build_ethan_salt_paper_handoff_package.py`
- Validation:
  - `python -m py_compile tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py tools/analyze/build_ethan_salt_paper_handoff_package.py`
  - `python tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_salt_hydraulic_evidence_subset_smoke`
  - `python tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_salt_hydraulic_evidence_subset`
  - `python tools/analyze/build_ethan_salt_paper_handoff_package.py --output-dir tmp/2026-06-18_ethan_salt_paper_handoff_package_smoke`
  - `python tools/analyze/build_ethan_salt_paper_handoff_package.py --output-dir reports/2026-06-18_ethan_salt_paper_handoff_package`

## Cross-Family Hydraulic Redesign Screen

After the Salt and Water family-only branch screens were both available, the
next step was not to fit a cross-family model. It was to ask a narrower design
question:

- if a future cross-family hydraulic redesign is attempted, should the direct
  branch observable stay as branch-mean direct `p_rgh` gradient, or move to
  cumulative direct branch-end `p_rgh` drop?

### Observed Output

- New bounded package:
  - `reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen`
- It published:
  - `overlap_case_time_audit.csv`
  - `overlap_case_summary.csv`
  - `overlap_family_summary.csv`
  - `direct_reduction_recommendations.csv`
  - `modeling_guardrails.md`

### Inferred Interpretation

- Shared clean Salt/Water overlap branches:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`
- Only `right_leg` emerged as a real bounded redesign candidate:
  - cumulative direct branch-end drop is preferred more often than the current
    branch-mean direct gradient in both families
- `test_section_span` stayed guarded:
  - both observables are sign-clean
  - the retained-time stability comparison does not show a decisive redesign
    advantage
- `upper_leg` exposed a different problem:
  - the cumulative direct branch-end drop is finite in the timeseries
  - but the current per-case summary terminal direct drop is missing
  - so future redesign work there must use the cumulative timeseries directly
    rather than trust `major_loss_summary.csv`

### Contradictions And Limits

- No branch was promoted to cross-family hydraulic readiness.
- The June 18 closure gate still applies:
  - `blocked_by_excluded_hydraulic_branch`
- `left_lower_leg` remains excluded because the Water side is excluded from the
  usable hydraulic subset.
- The redesign screen is therefore about future method choice, not current
  model-readiness.

### Scripts And Reproducibility

- Added:
  - `tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`
- Validation:
  - `python -m py_compile tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`
  - `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir tmp/2026-06-18_ethan_cross_family_hydraulic_redesign_screen_smoke`
  - `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen`

## Remaining science-side tasks closed without reopening extraction

Two small additive packages closed the remaining interpretation items that were
still open after the closure package, the family-only hydraulic screens, and
the cross-family redesign screen.

### Salt thermal model-surface ranking

- New package:
  - `reports/2026-06-18_ethan_salt_thermal_model_surface_ranking`
- This package stayed bounded to the already-defended Salt branch subset:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- Main decision:
  - primary Salt thermal modeling surface: `UA'(x)`
  - secondary Salt thermal modeling surface: `HTC(x)`
  - supporting-only: branch-averaged `R'_th`
  - diagnostic-only: `R'_th(x)`
- Why:
  - the safe subset remains genuinely well-supported
  - `UA'` and `HTC` are comparably stable
  - `UA'` is the cleaner branch-scale conductance surface
  - `R'_th` is visibly more fragile because the reciprocal transform amplifies
    the same low-conductance regions that already challenge `UA'`
- `right_leg` thermal behavior was not promoted.

### Pressure / feature / Water support note

- New package:
  - `reports/2026-06-18_ethan_pressure_feature_support_note`
- Main decisions:
  - feature `K_eff` stays `not_ready`
  - Water `test_section_span` stays `supporting_only`
  - hydro-corrected straight-section pressure rows stay `diagnostic_only`
- Why:
  - the June 17 feature package still relies on the stored `p_rgh` residual
    closure without a dedicated feature-path density integral
  - Water `test_section_span` is the strongest Water thermal branch, but it
    still does not clear the defended Salt driving-temperature gate
  - hydro-corrected pressure rows remain useful for methods context, but not
    yet for defended direct fitting

### Practical state after these additions

- The science-facing queue is now narrower.
- The next remaining method gap is the `upper_leg` summary-publication gap if a
  future cumulative-direct hydraulic redesign is pursued there.
- The next remaining writing move is still a separate claimed `../papers` task
  that uses the refreshed June 18 Salt handoff package and does not reopen any
  cross-family hydraulic claims.

## Convergence and Jin envelope run wave submitted

- Opened the new campaign root:
  - `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/`
- Staged eight continuation copies:
  - Salt 1 Jin and Salt 4 Jin from their latest prior continuation parents
  - Salt 2 Jin, Salt 3 Jin, and Water 1-4 from the staged modern source trees
- Verified the later DOE mutation path before writing it down:
  - case-level `heater_power_W` maps to the three lower heater patches
  - the separately powered test-section patch stays fixed in this first wave
  - cooler `h` and insulation thickness remain `0/T`-only DOE edits
- Direct local `sbatch` was unavailable on the current compute host, so all
  eight jobs were submitted through `login3.ls6.tacc.utexas.edu`
- Submitted jobs:
  - `3244955` Salt 1 Jin continuation, `120 h`
  - `3244951` Salt 2 Jin continuation, `120 h`
  - `3244950` Salt 3 Jin continuation, `120 h`
  - `3244954` Salt 4 Jin continuation, `120 h`
  - `3244953` Water 1 continuation, `72 h`
  - `3244957` Water 2 continuation, `72 h`
  - `3244952` Water 3 continuation, `72 h`
  - `3244956` Water 4 continuation, `72 h`
- Immediate queue check:
  - all eight jobs were `PD (Priority)` in `squeue`
- New provenance manifest:
  - `imports/2026-06-18_ethan_convergence_and_jin_envelope_wave.json`
- Monitoring plan:
  - Day 1: queue and bootstrap health
  - Day 2: first clean-write gate for the Jin-only Salt DOE children
  - Day 3: first convergence checkpoint
  - Day 4-5: reuse only runs with enough new late-window support
