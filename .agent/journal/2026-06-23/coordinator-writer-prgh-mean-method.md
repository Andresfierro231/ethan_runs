# AGENT-125 Raw Journal — p_rgh Mean Method And Presentation Breakdown

- date: `2026-06-23`
- role: `Coordinator / Writer`
- task ID: `AGENT-125`
- purpose:
  - document exactly how the June 23 `p_rgh(s)` versus `q_dyn(s)` figure means
    are built
  - add a slide-ready 1D performance breakdown by primary frozen case to the
    presentation package
- files inspected:
  - `.agent/BOARD.md`
  - `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/README.md`
  - `tools/analyze/build_ethan_prgh_vs_dynamic_profiles.py`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/best_full_coverage_case_metrics.csv`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/observable_leaderboard.csv`
  - `reports/2026-06-23_presentation/slide_outline.md`
  - `reports/2026-06-23_presentation/presentation_takeaways.md`
  - `reports/2026-06-23_presentation/README.md`
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-125.md`
  - `.agent/journal/2026-06-23/coordinator-writer-prgh-mean-method.md`
  - `imports/2026-06-23_ethan_prgh_mean_method_and_presentation_breakdown.json`
  - `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/README.md`
  - `reports/2026-06-23_presentation/slide_outline.md`
  - `reports/2026-06-23_presentation/presentation_takeaways.md`
  - `reports/2026-06-23_presentation/README.md`
- results or observations:
  - The mean profile in the `p_rgh`/`q_dyn` package is a binwise retained-time
    ensemble mean grouped by `(span_name, bin_index)`, not a smoothing pass
    along `s`.
  - The shaded envelope is the retained-time min/max at that same grouped bin,
    and the README now states that explicitly.
  - The current defended full-coverage 1D row misses all three primary frozen
    Salt cases materially; the presentation package now states that spread
    directly instead of only quoting the overall mean row.
  - The observable leaderboard also makes the hybrid caveat sharper: hybrid is
    only provisionally better on mass-flow, with `1` primary case of support,
    and still does not beat the defended baseline on mean temperature error.
