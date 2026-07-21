# Salt1 Terminal Harvest Admission Review

Date: `2026-07-13`

Task: `AGENT-283`

## Prompt

The user asked to perform terminal harvesting for ended jobs that are
essentially steady, following the earlier plan.

## Work Performed

Added a reusable builder:

`tools/analyze/build_terminal_harvest_admission_review.py`

The script consumes AGENT-280 final-window metrics and inspects the staged case
directories read-only for local solver/slurm logs and postProcessing family
coverage. It writes a dated package under:

`work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/`

## Observed Results

The review admits three Salt1 rows for terminal-harvest context:

| Case | Step | Decision |
| --- | --- | --- |
| `salt1_nominal` | `3282992.0` | `terminal_harvest_complete_context_only` |
| `salt1_lo10q` | `3288671.0` | `terminal_harvest_complete_context_only` |
| `salt1_hi10q` | `3288671.1` | `terminal_harvest_complete_context_only` |

`salt4_hi10q` remains excluded because it was not steady and was continued in
packed job `3293441`.

## Interpretation

This closes the terminal scheduler/log/postProcessing/admission-review gap for
the ended steady Salt1 rows. It does not promote Salt1 rows to closure-fit use,
does not edit the registry, and does not mutate native solver outputs.

## Validation

- `python3.11 -m unittest tools.analyze.test_terminal_harvest_admission_review`
- `python3.11 tools/analyze/build_terminal_harvest_admission_review.py`
- JSON validation for `summary.json` and the import manifest.
