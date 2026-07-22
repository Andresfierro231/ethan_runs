# Salt1 Terminal Harvest Admission Review

Task: `AGENT-283`

Generated: `2026-07-13T14:10:39-05:00`

## Purpose

This package performs the terminal scheduler/log/postProcessing/admission review
for ended Salt1 rows that AGENT-280 found essentially steady. It is a harvest
review, not a registry or closure-fit promotion.

## Scope

Included rows: `salt1_nominal`, `salt1_lo10q`, and `salt1_hi10q`.

Excluded row: `salt4_hi10q`, because AGENT-280 found it not steady and AGENT-274
continued it in packed job `3293441`.

## Outputs

- `scheduler_terminal_review.csv`: terminal state recorded from AGENT-280.
- `log_tail_review.csv`: read-only local solver/slurm log inventory and tail
  hints.
- `postprocessing_availability.csv`: postProcessing family coverage and latest
  numeric family time.
- `final_window_admission_review.csv`: final-window drift metrics collapsed to
  one row per Salt1 case.
- `admission_decision_table.csv`: compact harvest/admission decision table.
- `summary.json`: counts, thresholds, and source paths.

## Decision Boundary

`terminal_harvest_complete_context_only` means the ended row has terminal state,
postProcessing coverage, and a stationary final window. It does not change
closure-fit admission, registry state, or the Salt1 policy caveat.

## Reproduce

```bash
python3.11 tools/analyze/build_terminal_harvest_admission_review.py
python3.11 -m unittest tools.analyze.test_terminal_harvest_admission_review
```
