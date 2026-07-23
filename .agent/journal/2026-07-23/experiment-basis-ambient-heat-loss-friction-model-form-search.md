# Journal: Experiment-basis ambient heat-loss + friction model-form search

Date: 2026-07-23
Agent role: Forward-pred / Hydraulics / Thermal-modeling / Implementer / Tester / Writer / Reviewer
Task ID: TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23
Branch/worktree: main (no branch/worktree switch)

## Files inspected

- `.agent/BOARD.md` (own row only)
- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md`
  (style template) and its `refit_coefficients.csv`, `train_fit_quality.csv`,
  `holdout_external_score_old_vs_new.csv`
- `work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md`
  (style template) and its `friction_root_cause.csv`
- `.agent/status/2026-07-23_TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23.md`
  (status style template)
- `.agent/journal/2026-07-23/empirical-bias-salt1-4-refit-holdout-external-score.md`
  and `.agent/journal/2026-07-23/combined-best-current-model-temp-mdot-correction.md`
  (journal style templates)
- `imports/2026-07-23_combined_best_current_model_temp_mdot_correction.json`
  (manifest style template)
- `operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md`
  (operational-note style template)
- `tools/analyze/build_combined_best_current_model_temp_mdot_correction.py` and
  `tools/analyze/test_combined_best_current_model_temp_mdot_correction.py`
  (build/test script style templates)
- `.agent/BLOCKERS.md` (internal-Nu guardrail phrase, `thermal-cfd-1d-parity`
  entry)
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv`
  (M3 comparator row; checked M2_as_is/M3_as_is/D1-D4 diagnostic rows for
  context)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (read-only; F4 docstring line, F3_hagenbach/Shah(1978) citation, K_HAGENBACH
  constant)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
  (read-only; `t_ins_m` formula, `major_loss_multiplier` default,
  `internal_htc_mode`/`outer_closure_mode` fields)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv`
  (read-only; independently re-derived row count, TP/TW RMSE ranges, best
  mdot-error row, absence of a `friction_form` column)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/analysis/scenario_rankings.csv`,
  `scenario_plan.csv`, `RUN_SUMMARY.md` (read-only; independently re-derived
  row count, best TP RMSE, mean/std TW-excl-TW10 RMSE, per-segment insulation
  multiplier range 0.85-1.5x, absence of a `friction_form` column)
- `CLAUDE.md` (checked neither prior sweep's name appears here)
- `work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv`
  (spot-checked `measured_K` column exists as this package's scoring basis)
- Grepped the whole repo for both prior sweep names and found two additional
  contexts not mentioned in the task prompt
  (`.agent/status/2026-06-19_AGENT-090.md`,
  `reports/2026-06/2026-06-19/2026-06-19_ethan_litrev_to_1d_modeling_handoff/dual_path_execution_report.md`)
  -- read both to confirm they are exploration/read-list/anchor-list
  mentions, not analysis of the TP/TW-stuck finding, and documented this
  honest nuance rather than an unqualified "never referenced anywhere" claim.

## Files changed

- `tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py` (new)
- `tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py` (new)
- `work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search/`
  (new package: README.md, summary.json, friction_closure_comparison.csv,
  mdot_temperature_decoupling_check.csv, prior_undocumented_sweeps_found.csv,
  sign_convention_corrections.csv, insulation_screening_sweep.csv,
  insulation_friction_zero_crossing_refinement.csv,
  salt1_4_train_validation_at_recommended_combo.csv,
  validation_case_scores_raw_physics.csv,
  residual_correction_on_physics_baseline.csv, internal_nu_ablation.csv,
  physical_plausibility_caveats.csv, claim_boundary_table.csv,
  validation_exposure_count.csv, validation_terminology_crosswalk.csv,
  source_manifest.csv, no_mutation_guardrails.csv)
- `.agent/status/2026-07-23_TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23.md` (new)
- `.agent/journal/2026-07-23/experiment-basis-ambient-heat-loss-friction-model-form-search.md` (this file)
- `imports/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search.json` (new)
- `operational_notes/07-26/23/2026-07-23_EXPERIMENT_BASIS_AMBIENT_HEAT_LOSS_FRICTION_MODEL_FORM_SEARCH.md` (new)
- `.agent/BOARD.md` (own row status only)

## Commands run

```
python3 -m py_compile tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py \
  tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py
python3 tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py
python3 tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py
```

Prior to writing the build script, exploratory (not committed) `python3`
one-liners and `grep`/`wc -l` checks against the read-only source CSVs were
used to independently re-derive:

- the historical friction-closure benchmark mean percentages
  (32.575/15.8325/11.82 for F1/F3_shah_apparent/F3_hagenbach, matching the
  task's stated 32.6%/15.8%/11.8% to rounding);
- `joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv`:
  64 data rows, `mean_tp_rmse_K` range 67.63890775397246-68.56583595431157,
  `mean_tw_no_tw10_rmse_K` range 64.92415505987299-65.51420445769101, best
  `mean_mass_flow_relative_error_pct` abs value 0.010532337829829727% -- all
  matching the task's stated ranges;
- `practical_reduced_order_broadened_v1/analysis/scenario_rankings.csv`: 12
  rows, best `mean_tp_rmse_K`=59.99248870084229, and its own
  `RUN_SUMMARY.md`: "Mean TW RMSE excluding TW10: `65.8969 K` with
  `std=13.1459`" -- both matching the task's stated 59.99/65.897/13.146;
- `practical_reduced_order_broadened_v1/scenario_plan.csv`'s
  `outer_insulation_multiplier_by_parent_segment` dict values span
  {0.85, 0.9, 0.95, 1.4, 1.5} -- confirming and sharpening the task's "0.85-
  1.5x" characterization of the untested-magnitude claim (this was not
  explicit in the task text; found it by inspecting the actual scenario-plan
  dict values, since the top-level `scenario_rankings.csv` only carries the
  coarser global `insulation_thickness_in` in {1.0, 2.0});
- neither sweep's CSV header row contains a `friction_form` column,
  confirming the "neither sweep varied friction_form" claim;
- `.agent/BLOCKERS.md` contains the internal-Nu guardrail phrase verbatim;
- `friction_closures.py` contains the exact F4 docstring line and the
  Shah (1978)/K_HAGENBACH citation verbatim;
- `solver.py` contains the exact `t_ins_m` formula and
  `major_loss_multiplier: float = 1.0` default verbatim;
- `master_model_form_scoreboard.csv`'s M3 row has
  `tp_rmse_or_error_K=13.558`, `tw_rmse_or_error_K=18.9775`,
  `model_form_name=segment_only_fluid_walls`, matching the task's citation.

## Results / observations

- Every independently-checkable number in the task prompt matched its cited
  source file. The F1-based F2 offset in the task prompt was given to
  ~11-12 significant figures; the file of record
  (`refit_coefficients.csv`) has `b=138.28222646893293` to full float
  precision. This build script and its tests cite the FILE value as
  authoritative (verified via `verify_f1_based_f2_temperature_correction()`)
  rather than re-typing a long float from the task prompt by hand, to avoid
  introducing a transcription error of its own.
- The two prior undocumented sweeps' TP/TW-stuck findings are now fully
  independently reproducible from their own CSVs (not just cited from the
  task prompt), and the "never referenced in CLAUDE.md or the thesis
  scoreboard" claim held up exactly as stated -- but a repo-wide grep found
  the file *paths* (not the TP/TW-stuck finding) already appear in two other
  places (a command-list status file, a report anchor list). Documented this
  honest nuance in `prior_undocumented_sweeps_found.csv`'s `caveat` column
  rather than repeating the task's slightly-too-strong "never referenced"
  framing unqualified.
- All twelve findings from the task prompt are documented with explicit
  provenance tagging distinguishing (a) numbers independently re-verified
  against a reachable repo file from (b) numbers that are session-only
  ad hoc `solve_case()` results, reproducible only by re-running the solver.
- The internal-Nu ablation (finding 10) and the corrected-direction
  insulation/friction sweep (findings 5-7) are presented with an explicit
  "what this proves vs. what remains a hypothesis" framing distinguishing
  the decisive/rigorous internal-Nu ruling-out from the calibrated/
  needs-rig-verification insulation~8% finding, per the task's explicit
  instruction not to conflate the two evidentiary strengths.
- The off-scope-for-CFD-main-body banner, "validation" terminology
  crosswalk, and cross-reference to the CFD-basis package as a "parallel
  main-body track using different reference data" (not
  superseded/superseding) are all present in the README frontmatter and
  body, per the task's explicit framing instructions.
- All 13 checks in the new test script pass, including internal-consistency
  checks (friction-form means, Salt1-4 mean-at-recommended-combo, internal-Nu
  monotonicity/gap) and citation-accuracy checks (F1-based F2 coefficients,
  M3 comparator, guardrail phrase, F4 docstring line, both prior-sweep
  numeric claims).

## Incomplete lines of investigation

- No new solver runs were performed by this task (per its board-row
  guardrails); the friction-form default has not actually been changed in
  any candidate config, and the recommended combo
  (`friction_form=F3_hagenbach`, `insulation_multiplier=0.08`,
  `major_loss_multiplier=0.6`) has not been re-run outside this session's
  ad hoc exploration.
- The val_salt2 property-basis discrepancy (finding 8; this package used
  `salt_current`, the parallel CFD-basis session found `salt_jin` is
  methodologically consistent) is flagged but not resolved here.
- The insulation~8%-of-nameplate hypothesis has not been checked against any
  physical/photographic evidence of the rig's actual insulation condition.

## Next steps

- None required from this task itself; package is complete and
  self-contained. Handoff notes are in the status file's Follow-up section
  and the operational note's "Next task sequence."
