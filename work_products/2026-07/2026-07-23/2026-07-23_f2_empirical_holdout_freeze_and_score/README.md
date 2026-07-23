---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv
tags: [track-a, empirical-rom, F2, freeze, score-once, holdout, thesis, diagnostic-only]
related:
  - .agent/status/2026-07-23_TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23.md
  - .agent/journal/2026-07-23/f2-empirical-holdout-freeze-and-score-harness.md
  - operational_notes/07-26/23/2026-07-23_F2_EMPIRICAL_HOLDOUT_FREEZE_AND_SCORE_HARNESS.md
  - work_products/2026-07/2026-07-23/2026-07-23_thesis_two_track_rom_model_writeup/README.md
task: TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23
date: 2026-07-23
role: Implementer / Tester / Writer / Reviewer
owner: claude
type: work_product
status: complete
---

# F2 Empirical Holdout Freeze + Score-Once Harness

Decision: `f2_frozen_and_score_harness_ready_holdout_score_blocked_pending_target_extraction`.

This package advances Track A (empirical bias-corrected ROM) toward its first
*legal protected-holdout score* by doing the parts that are legal, correct, and
needed regardless of anything else, without fabricating a number.

## What was done

1. **F2 frozen (pre-registration).** `f2_freeze_manifest.csv` records the
   immutable frozen form `T_corrected = a*T_1D + b` with
   `a = 0.3729829182408737`, `b = 246.55192842685844` (2 DOF, fit on
   Salt1/Salt2 train-support rows only, 32 fit rows), plus the legal runtime
   input contract, split labels, and a `content_sha256` over the
   frozen-coefficients source + the builder. This locks F2 *before* any holdout
   contact, satisfying freeze-before-score discipline.
2. **Score-once harness built + dry-run validated.** `score_rows()` applies the
   frozen affine and computes per-sensor error, RMSE, MAE. `score_harness_dry_run.csv`
   exercises it on the **Salt_2 nominal** validation table (NOT a holdout):
   corrected RMSE `16.46 K` vs raw 1D bias (~90 K), affine-identity check passed.
   This proves harness correctness with zero holdout contact.
3. **Readiness ledger.** `holdout_score_readiness.csv` states, per protected
   target, exactly what is missing.

## The score is NOT computable yet — exact remaining inputs

| target | split role | missing inputs | gap type |
|--------|-----------|----------------|----------|
| `salt2_lo5q`, `salt2_hi5q` | primary blind holdout | (i) 1D `T_1D` at TP/TW sensors for ±5Q; (ii) **TP/TW CFD sensor targets** (only upcomer-plane targets exist) | (i) cheap 1D; (ii) **CFD postprocessing on existing runs (no new solve)** |
| `val_salt2` | external test | (i)+(ii) above, plus a compatible sensor-level external-test admission artifact (does not exist) | harder-blocked |

The single blocker for the primary holdout is **TP/TW CFD sensor target
extraction for Salt2±5Q** from the already-completed corrected runs. Once that
and the 1D ±5Q predictions land, the harness scores once and the thesis gets its
first genuine protected-holdout number.

## Claim boundary (non-negotiable)

F2 is an **empirical discrepancy ROM**, not a physical closure
(mf11: `empirical_diagnostic_only`). Allowed: report F2's transfer/holdout error
as calibrated-discrepancy performance for a digital-twin ROM layer. Forbidden:
call F2 coefficients admitted heat-transfer coefficients, a physical closure, or
conflate it with the strict Track-B physical model. No refit or model selection
after freeze.

## Outputs
| file | content |
|------|---------|
| `f2_freeze_manifest.csv` | immutable frozen F2 (a, b, DOF, fit provenance, input contract, content hash, claim boundary) |
| `score_harness_dry_run.csv` | nominal-data correctness validation of the score-once harness |
| `holdout_score_readiness.csv` | per-target missing inputs + gap type |
| `decision.csv` | overall decision + blockers |
| `no_mutation_guardrails.csv` | 15 guardrails, all False |
| `source_manifest.csv`, `summary.json` | provenance + rollup |

## Reproduce
```
python3.11 tools/analyze/build_f2_empirical_holdout_freeze_and_score.py
python3.11 -m pytest tools/analyze/test_f2_empirical_holdout_freeze_and_score.py -q
```

## Next
1. Generate frozen 1D `T_1D` predictions for `salt2_lo5q`/`salt2_hi5q` at the
   TP/TW sensor placements (run `tamu_loop_model_v2` at the ±5Q BC; blind).
2. Extract TP/TW CFD sensor targets for Salt2±5Q from the corrected runs
   (CFD postprocessing, no new solve) — the controlling blocker.
3. Fire the harness once; report pass/fail as empirical-ROM holdout performance.
4. `val_salt2` external score needs its missing sensor-level external artifact.
