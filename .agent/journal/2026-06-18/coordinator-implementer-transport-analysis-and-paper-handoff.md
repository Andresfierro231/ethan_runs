# AGENT-072 Raw Journal

- date: `2026-06-18`
- role: `Coordinator / Implementer`
- task: build a thorough all-runs transport analysis package, determine what needs to be staged, and stop at a Salt-paper handoff package rather than editing `../papers`

## Observed State At Start

- The June 17 scrutiny package already existed and was the right gate to build on.
- `reports/2026-06-17_ethan_transport_scrutiny_package/paper_safe_asset_map.csv` still identified the same Salt-safe thermal subset:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- `reports/2026-06-17_ethan_transport_scrutiny_package/transport_contradiction_log.csv` still had two `requires_code_fix = yes` hydraulic rows:
  - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
  - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- `../papers/.agent/BOARD.md` remained unassigned, so a paper-side implementation was intentionally out of scope.

## Analysis Package Implementation

- Added `tools/analyze/build_ethan_transport_analysis_package.py`.
- Inputs:
  - June 17 scrutiny package
  - June 15 representative Salt 2 package
  - June 15 Salt-family campaign
  - June 15 all-runs campaign
  - June 17 math reference
  - June 17 interpretation package
- Outputs at `reports/2026-06-18_ethan_transport_analysis_package/`:
  - `case_family_interpretation_matrix.csv`
  - `transport_contradiction_priority.csv`
  - `promotion_candidate_index.csv`
  - branch-trust heatmaps for all-runs, Salt, and Water
  - hydraulic hotspot figure
  - Salt and Water safe-branch support figures
  - `README.md`
  - `summary.json`

## Handoff Package Implementation

- Added `tools/analyze/build_ethan_salt_paper_handoff_package.py`.
- Scope intentionally stayed Salt-only and staged assets for later manuscript import without touching `../papers`.
- Generated at `reports/2026-06-18_ethan_salt_paper_handoff_package/`:
  - `staged_assets_manifest.csv`
  - `figure_claim_map.csv`
  - `table_claim_map.csv`
  - `README.md`
  - `staged_assets_readme.md`
  - `summary.json`
- Staged main-text or candidate-main-text figures:
  - Salt 2 heat-loss subset
  - Salt 4 heat-loss subset
  - Salt 2 azimuthal subset
  - Salt 4 azimuthal subset
  - Salt 2 hydraulic mechanism figure with Darcy-f zoom
  - Salt 2 effective-thermal figure copied from representative package
  - Salt 2 branch-thermal safe-subset figure
  - Salt-family branch-thermal safe-subset figure focused on Salt 2 / Salt 4 and safe branches
- Staged appendix-support figures:
  - Salt branch-trust heatmap
  - Salt safe-branch QC support figure

## Failure-Oriented Iteration

- First handoff smoke build failed because `zip(..., strict=True)` is not supported on this runtime.
- Fixed by removing the `strict=True` keyword and reran successfully.
- Also fixed the figure-bundle copy logic so it reads report figure trees from `figures/<fmt>/<stem>.<fmt>` rather than assuming all formats sit in one directory.

## Validation

- `python -m py_compile tools/analyze/build_ethan_transport_analysis_package.py`
- `python -m py_compile tools/analyze/build_ethan_salt_paper_handoff_package.py`
- `python tools/analyze/build_ethan_transport_analysis_package.py --output-dir tmp/2026-06-18_ethan_transport_analysis_package_smoke`
- `python tools/analyze/build_ethan_salt_paper_handoff_package.py --analysis-dir tmp/2026-06-18_ethan_transport_analysis_package_smoke --output-dir tmp/2026-06-18_ethan_salt_paper_handoff_package_smoke`
- `python tools/analyze/build_ethan_transport_analysis_package.py --output-dir reports/2026-06-18_ethan_transport_analysis_package`
- `python tools/analyze/build_ethan_salt_paper_handoff_package.py --analysis-dir reports/2026-06-18_ethan_transport_analysis_package --output-dir reports/2026-06-18_ethan_salt_paper_handoff_package`

## Key Results

- The analysis package reports:
  - `promotion_stage_now_count = 7`
  - `priority_one_contradiction_count = 2`
- The handoff package stages:
  - `12` total assets
  - `8` main-text or candidate-main-text assets
  - `2` appendix-support assets
- The handoff stays consistent with the scrutiny gate:
  - no boundary-layer headline promotion
  - no all-runs cross-family figure promotion into the Salt paper
  - branch thermal restricted to `left_lower_leg`, `test_section_span`, `left_upper_leg`, and `upcomer`

## Remaining Next Actions

- Open a separate `../papers` task before any `3d_analysis` edits.
- Use only:
  - `reports/2026-06-18_ethan_salt_paper_handoff_package/staged_assets_manifest.csv`
  - `reports/2026-06-18_ethan_salt_paper_handoff_package/figure_claim_map.csv`
  - `reports/2026-06-18_ethan_salt_paper_handoff_package/table_claim_map.csv`
  as the promotion surface.
- Investigate the two water `left_lower_leg` hydraulic contradiction rows before strengthening cross-family hydraulic claims.

## Focused Scientific Interpretation Follow-On

- Added `tools/analyze/build_ethan_transport_scientific_interpretation_package.py`.
- Kept the scope deliberately narrow:
  - no new extraction
  - no new campaign builder
  - no dashboard refresh
  - only direct interpretation of the existing June 15/17/18 package stack
- New durable package:
  - `reports/2026-06-18_ethan_transport_scientific_interpretation_package/`
- New smoke package:
  - `tmp/2026-06-18_ethan_transport_scientific_interpretation_package_smoke/`

### What the new package actually resolved

- Water 1 `left_lower_leg` hydraulic contradiction:
  - diagnosed as a weak-signal wall-registered `p_rgh` problem
  - branch-end cumulative direct `p_rgh` drop stays positive
  - branch-mean direct gradient changes sign because mixed-sign local direct bins nearly cancel
  - outcome: `resolved_exclude`
- Water 2 `left_lower_leg` hydraulic contradiction:
  - diagnosed as weak direct `p_rgh` signal plus mixed `flow_alignment_sign` in one retained time
  - branch-end cumulative direct `p_rgh` drop stays positive
  - branch-mean direct reduction is not mechanically traceable to one stable sign convention
  - outcome: `unresolved_exclude`

### Thermal interpretation outcomes

- Salt-only safe effective-thermal branch subset stayed unchanged and was reaffirmed:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- Salt `right_leg` remained blocked from headline thermal use.
- Water `left_lower_leg` remained blocked by small `|T_bulk - T_wall|` and low usable fraction.
- Water `test_section_span` remained the cleanest Water branch, but only at supporting/contextual level rather than headline-safe level.

### New output set

- `README.md`
- `interpretation_summary.json`
- `contradiction_resolution_rows.csv`
- `branch_thermal_interpretation.csv`
- `scientific_conclusions.csv`
- `internal_only_decisions.csv`
- `cross_family_claims_audit.csv`
- `methods_interpretation.md`
- `model_dependency_readiness.md`
- `remaining_blockers.md`

### Validation

- `python -m py_compile tools/analyze/build_ethan_transport_scientific_interpretation_package.py`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir tmp/2026-06-18_ethan_transport_scientific_interpretation_package_smoke`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir reports/2026-06-18_ethan_transport_scientific_interpretation_package`

### Immediate boundary after this pass

- Cross-family hydraulic dependency construction remains blocked.
- Salt-only effective thermal dependency construction is now explicitly support-gated and branch-bounded.
- Water thermal dependency construction remains blocked on the left-side return path.

## Interpretation Closure Follow-On

- Added `tools/analyze/build_ethan_transport_interpretation_closure.py`.
- Kept the scope bounded to one scientific closure action:
  - no new extraction
  - no new campaign rebuild
  - no new dashboard layer
  - only one forensic audit of `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- New durable package:
  - `reports/2026-06-18_ethan_transport_interpretation_closure/`
- New smoke package:
  - `tmp/2026-06-18_ethan_transport_interpretation_closure_smoke/`

### What changed relative to the June 18 focused interpretation package

- Water 2 `left_lower_leg` moved from `unresolved_exclude` to
  `resolved_exclude`.
- The closure decision is based on:
  - positive branch-end cumulative direct `p_rgh` drop in every retained time
  - exactly one retained time carrying the non-modal branch alignment sign
  - the remaining branch-mean sign flips being weak-signal local cancellation
    artifacts
- Cross-family hydraulic gating changed from:
  - `blocked_by_unresolved_hydraulic_contradiction`
  to:
  - `blocked_by_excluded_hydraulic_branch`

### New closure outputs

- `water2_left_lower_leg_hydraulic_audit.csv`
- `water2_left_lower_leg_hydraulic_audit.md`
- revised `contradiction_resolution_rows.csv`
- revised `scientific_conclusions.csv`
- revised `cross_family_claims_audit.csv`
- revised `methods_interpretation.md`
- revised `model_dependency_readiness.md`
- revised `remaining_blockers.md`

### Validation

- `python -m py_compile tools/analyze/build_ethan_transport_interpretation_closure.py`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir tmp/2026-06-18_ethan_transport_interpretation_closure_smoke`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir reports/2026-06-18_ethan_transport_interpretation_closure`

### Immediate boundary after the closure pass

- Water `left_lower_leg` remains excluded from usable hydraulic model evidence.
- Cross-family hydraulic dependency work remains blocked, but no longer because
  of an unresolved sign mystery on Water 2.
- The Salt safe thermal subset remains unchanged:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`

## Water Hydraulic Evidence Subset Follow-On

- Added `tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`.
- Kept the scope additive and narrow:
  - no new extraction
  - no package rebuild
  - no cross-family promotion
  - only a Water-family branch-pressure evidence screen using the current
    package outputs plus the June 18 interpretation closure
- New durable package:
  - `reports/2026-06-18_ethan_water_hydraulic_evidence_subset/`
- New smoke package:
  - `tmp/2026-06-18_ethan_water_hydraulic_evidence_subset_smoke/`

### What the subset package concluded

- Water-family hydraulic candidates:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`
- Water-family contextual-only branches:
  - `lower_leg`
  - `left_upper_leg`
- Water-family excluded branch:
  - `left_lower_leg`

### Why the contextual branches were not promoted

- `lower_leg`:
  - one retained-time direct sign failure in Water 4 under weak direct signal
- `left_upper_leg`:
  - one retained time in Water 2 with non-positive cumulative direct branch-end
    `p_rgh` drop

### Validation

- `python -m py_compile tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_water_hydraulic_evidence_subset_smoke`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_water_hydraulic_evidence_subset`

### Immediate boundary after the Water subset pass

- Water-family hydraulic work can now stay off the excluded `left_lower_leg`
  branch, but the package explicitly keeps all Water candidates out of
  cross-family readiness.

## Salt Hydraulic Evidence Subset Follow-On

- Added `tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py`.
- Kept the scope parallel to the Water subset package:
  - no new extraction
  - no package rebuild
  - no cross-family promotion
  - only a Salt-family branch-pressure evidence screen using the existing Salt
    case packages, the current Water subset, and the June 18 interpretation
    closure
- New durable package:
  - `reports/2026-06-18_ethan_salt_hydraulic_evidence_subset/`
- New smoke package:
  - `tmp/2026-06-18_ethan_salt_hydraulic_evidence_subset_smoke/`

### What the Salt subset package concluded

- Salt-family hydraulic candidates:
  - `lower_leg`
  - `right_leg`
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upper_leg`
- Shared clean Salt/Water overlap:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`

### Why the overlap is still guarded

- The overlap rows are clean in both family screens, but the closure package
  still blocks direct cross-family hydraulic promotion.
- `left_lower_leg` remains unusable for overlap because the Water side is
  excluded.
- `lower_leg` and `left_upper_leg` remain Salt-only candidates because the
  current Water screen only supports contextual use on those branches.

### Validation

- `python -m py_compile tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py`
- `python tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_salt_hydraulic_evidence_subset_smoke`
- `python tools/analyze/build_ethan_salt_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_salt_hydraulic_evidence_subset`

## Closure-Aware Salt Paper Handoff Refresh

- Refreshed `tools/analyze/build_ethan_salt_paper_handoff_package.py` without
  changing the staged Salt asset set.
- New behavior:
  - the handoff package now records
    `reports/2026-06-18_ethan_transport_interpretation_closure/README.md` as
    the current science gate
  - the handoff README and summary now carry the closure status
    `blocked_by_excluded_hydraulic_branch`
  - the package now writes `closure_gate_note.md` so later paper work can see
    that the contradiction queue is closed but the cross-family hydraulic gate
    is still blocked by exclusion

### Validation

- `python -m py_compile tools/analyze/build_ethan_salt_paper_handoff_package.py`
- `python tools/analyze/build_ethan_salt_paper_handoff_package.py --output-dir tmp/2026-06-18_ethan_salt_paper_handoff_package_smoke`
- `python tools/analyze/build_ethan_salt_paper_handoff_package.py --output-dir reports/2026-06-18_ethan_salt_paper_handoff_package`

### Immediate boundary after this refresh

- The Salt paper-facing staging surface remains valid and Salt-only.
- The next direct manuscript edit still requires a separate claimed `../papers`
  task.
- The closure-aware handoff now makes it explicit that future paper text should
  avoid cross-family hydraulic framing because the gate is blocked by excluded
  Water evidence, not by an unresolved sign mystery.

## Cross-Family Hydraulic Redesign Screen

- Added `tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`.
- Kept the scope bounded:
  - no new extraction
  - no package rebuild
  - no campaign rebuild
  - no cross-family model fit
  - only a redesign-feasibility audit on the shared clean Salt/Water overlap
    branches using the existing Salt subset, Water subset, and closure package
- New durable package:
  - `reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen/`
- New smoke package:
  - `tmp/2026-06-18_ethan_cross_family_hydraulic_redesign_screen_smoke/`

### What the redesign screen actually tested

- Shared overlap branches:
  - `right_leg`
  - `test_section_span`
  - `upper_leg`
- For each branch and case:
  - retained-time mean direct `p_rgh` gradient
  - retained-time terminal cumulative direct `p_rgh` drop
  - retained-time stability via relative coefficient of variation
- The question was not “is this branch cross-family ready?”
- The question was only:
  - does cumulative direct branch-end drop behave better than the current
    branch-mean direct gradient if a future redesign is attempted?

### What the package concluded

- `right_leg`:
  - `bounded_cumulative_redesign_candidate`
  - both families prefer cumulative direct branch-end drop more often than the
    branch-mean direct gradient on the retained-time stability screen
- `test_section_span`:
  - `no_clear_redesign_priority`
  - both observables are sign-clean, but the retained-time stability screen
    does not show a decisive redesign advantage
- `upper_leg`:
  - `timeseries_only_do_not_use_summary_terminal_drop`
  - the cumulative direct branch-end drop is finite in the timeseries, but the
    current per-case summary terminal direct drop remains missing in one or
    both families, so any future redesign there must read the cumulative
    timeseries directly rather than trust `major_loss_summary.csv`

### Validation

- `python -m py_compile tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`
- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir tmp/2026-06-18_ethan_cross_family_hydraulic_redesign_screen_smoke`
- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen`

### Immediate boundary after the redesign screen

- No branch became cross-family-ready from this pass.
- `right_leg` is the only justified starting point if a future cumulative-direct
  redesign is pursued.
- `test_section_span` should stay on the current guarded path until a stronger
  redesign need appears.
- `upper_leg` first needs the summary-publication gap reconciled before it can
  support a clean redesign comparison.

- Water-only branch-pressure work now has a bounded candidate subset.
- Cross-family hydraulic work remains blocked because no Water branch from this
  subset has yet been paired to a separate Salt-side hydraulic screen.

## Salt Thermal Model Surface Ranking

- Added `tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py`.
- Kept the scope bounded:
  - no new extraction
  - no case rebuild
  - no campaign rebuild
  - only Salt, and only the already-defended safe branch subset
- New durable package:
  - `reports/2026-06-18_ethan_salt_thermal_model_surface_ranking/`
- New smoke package:
  - `tmp/2026-06-18_ethan_salt_thermal_model_surface_ranking_smoke/`

### What the ranking actually tested

- Existing defended Salt branches only:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- Existing branch-summary support metrics only:
  - usable fraction
  - warning fraction
  - minimum resolved `|T_bulk - T_wall|`
  - case-to-case relative variability in mean branch `HTC`, `UA'`, and `R'_th`

### What the package concluded

- Primary Salt thermal modeling surface:
  - `effective_ua_profile`
- Secondary Salt thermal modeling surface:
  - `effective_htc_profile`
- Supporting-only:
  - `branch_average_thermal_resistance`
- Diagnostic-only:
  - `thermal_resistance_profile`

The reason is not that `R'_th` is meaningless. The reason is that the
reciprocal transform is visibly more fragile on the same safe subset, while
`UA'` remains the most direct branch-scale conductance surface and avoids the
extra wall-area normalization choice embedded in `HTC`.

### Validation

- `python -m py_compile tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py`
- `python tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py --output-dir tmp/2026-06-18_ethan_salt_thermal_model_surface_ranking_smoke`
- `python tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py --output-dir reports/2026-06-18_ethan_salt_thermal_model_surface_ranking`

## Pressure / Feature / Water Support Note

- Added `tools/analyze/build_ethan_pressure_feature_support_note.py`.
- Reused the existing June 17 pressure / HTC / boundary-layer package instead of
  building another broad package.
- New durable package:
  - `reports/2026-06-18_ethan_pressure_feature_support_note/`
- New smoke package:
  - `tmp/2026-06-18_ethan_pressure_feature_support_note_smoke/`

### What the follow-on note actually closed

- Whether feature `K_eff` is ready for any family-specific dependency use
- Whether Water `test_section_span` should be promoted above supporting-only
- Whether hydro-corrected straight-section pressure rows can be treated as
  defended direct observables

### What the package concluded

- Feature `K_eff` stays `not_ready`
- Water `test_section_span` stays `supporting_only`
- Hydro-corrected straight-section pressure rows stay `diagnostic_only`

The key reason feature `K_eff` remains blocked is unchanged: the preserved June
17 package still uses the stored `p_rgh` residual closure without a dedicated
feature-path density integral. The key reason Water `test_section_span` remains
supporting-only is also unchanged: it is the strongest Water thermal branch,
but it still does not clear the defended Salt driving-temperature gate.

### Validation

- `python -m py_compile tools/analyze/build_ethan_pressure_feature_support_note.py`
- `python tools/analyze/build_ethan_pressure_feature_support_note.py --output-dir tmp/2026-06-18_ethan_pressure_feature_support_note_smoke`
- `python tools/analyze/build_ethan_pressure_feature_support_note.py --output-dir reports/2026-06-18_ethan_pressure_feature_support_note`

## 2026-06-18 17:05 CDT run-wave implementation

### Scope

- Added a bounded campaign root:
  - `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/`
- Added tracked artifacts:
  - `README.md`
  - `TODO.md`
  - `campaign_manifest.csv`
  - `doe_scaffold_notes.md`
  - `scripts/run_continuation_generic_openfoam13.sbatch`
  - `imports/2026-06-18_ethan_convergence_and_jin_envelope_wave.json`

### Observed output

- Staged eight continuation copies:
  - Salt 1 / Salt 4 Jin from the latest prior continuation parents
  - Salt 2 / Salt 3 Jin from staged modern sources
  - Water 1-4 from staged modern sources
- Verified and documented the later DOE mutation path:
  - case-level `heater_power_W` corresponds to the three lower heater patches
  - the separately powered test-section patch remains fixed in this first wave
- Direct local `sbatch` was blocked on compute host
  `c318-008.ls6.tacc.utexas.edu`, so the already-approved `ssh login3 ... sbatch`
  path was used for all job launches.

### Submitted jobs

- Salt Jin, `120 h` each:
  - `3244955` `ethan_s1j_cont`
  - `3244951` `ethan_s2j_cont`
  - `3244950` `ethan_s3j_cont`
  - `3244954` `ethan_s4j_cont`
- Water, `72 h` each:
  - `3244953` `ethan_w1_cont`
  - `3244957` `ethan_w2_cont`
  - `3244952` `ethan_w3_cont`
  - `3244956` `ethan_w4_cont`

### Queue confirmation

- Ran:
  - `ssh login3.ls6.tacc.utexas.edu "squeue -j 3244950,3244951,3244952,3244953,3244954,3244955,3244956,3244957"`
- Current state:
  - all eight jobs are `PD (Priority)`

### Boundaries preserved

- No DOE child jobs were submitted in this pass.
- No numerics, mesh, turbulence, or property-model settings were changed.
- Water remains continuation/convergence-only in this wave.
- The first Jin envelope children remain gated on at least one clean new parent write.
