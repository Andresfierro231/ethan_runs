# Journal: F2 empirical holdout freeze + score-once harness

Date: `2026-07-23`
Role: Implementer / Tester / Writer / Reviewer
Task ID: `TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23`

## Context
User wants final model forms into the LaTeX thesis. Four scoping scans established
the two-track thesis (Track A empirical bias ROM = F2/F5; Track B strict physical
= fluid+walls/PASSIVE-H2/M6 blocked). No form has a true protected-holdout score.
User endorsed "two-track + empirical F2 score" as the fast path to a real number.
A readiness scan then found the empirical score is NOT analysis-only: it needs a
freeze manifest + 1D holdout predictions + TP/TW CFD target extraction for Salt2
+/-5Q (the existing pm5 targets are upcomer-plane, not TP/TW). I did the legal,
correct, always-needed parts now and scoped the one compute blocker.

## Files inspected (read-only)
- `.../2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv` (F2 a/b, 32 fit rows)
- `.../2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv` (TP/TW schema, predicted_K/measured_K)

## Files changed
- NEW `tools/analyze/build_f2_empirical_holdout_freeze_and_score.py` + test
- NEW `work_products/2026-07/2026-07-23/2026-07-23_f2_empirical_holdout_freeze_and_score/**`
- `.agent/BOARD.md` (own row), status, this journal, import, operational_notes note.

## Commands run
```
python3.11 tools/analyze/build_f2_empirical_holdout_freeze_and_score.py
python3.11 -m pytest tools/analyze/test_f2_empirical_holdout_freeze_and_score.py -q
```

## Results / observations
- F2 frozen: a=0.3729829182408737, b=246.55192842685844; content_sha256
  3f4cc72f...; immutable, physical_closure_claim_allowed=False.
- Harness dry-run on Salt_2 nominal: corrected RMSE 16.46 K vs raw ~90 K bias;
  affine identity check passed. (Nominal = in-sample; validates correctness only,
  NOT a holdout score.)
- 0 protected rows scored. Readiness: Salt2 +/-5Q blocked on 1D +/-5Q predictions
  + TP/TW CFD target extraction; val_salt2 blocked additionally on external
  artifact.
- 6 tests pass; 15 guardrails False.

## Corrected premise (important)
My earlier "empirical score = cheap 1D + join, no CFD" was wrong: the Salt2 +/-5Q
TP/TW sensor targets do not exist and must be extracted from the corrected CFD
runs (postprocessing, no new solve). The freeze + harness done here are still the
right first step and will be reused verbatim once targets land.

## Next steps
See status Follow-up: 1D +/-5Q predictions -> TP/TW CFD target extraction ->
score once -> evidence-packet + LaTeX transfer.
