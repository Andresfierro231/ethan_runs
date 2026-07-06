# AGENT-124 Raw Journal — Presentation 1D Section

- date: `2026-06-23`
- role: `Coordinator / Writer`
- task ID: `AGENT-124`
- purpose:
  - add slide-ready 1D-modeling content to the June 23 presentation package
  - make the current model setup, comparison metrics, and interpretation
    boundaries easy to present without reopening analysis
- questions accumulating:
  - Once the exact June 23 latest-window freeze lands, do we want to swap the
    presentation-local 1D section to that newer contract immediately, or keep
    this section locked to the already-published June 23 local bakeoff until a
    refreshed external `Fluid` rerun exists too?
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-124.md`
  - `.agent/journal/2026-06-23/coordinator-writer-presentation-1d-section.md`
  - `reports/2026-06-23_presentation/README.md`
  - `reports/2026-06-23_presentation/slide_outline.md`
  - `reports/2026-06-23_presentation/presentation_takeaways.md`
  - `reports/2026-06-23_presentation/1d_model_slide_sequence.md`
  - `reports/2026-06-23_presentation/1d_model_results_tables.md`
  - `reports/2026-06-23_presentation/1d_model_setup_documentation.md`
- results or observations:
  - The presentation package now has a self-contained 1D subsection that can
    be dropped into the deck without reopening the larger report.
  - The strongest slide-ready negative result remains the same: the best
    full-coverage readable 1D row still misses by about `11.27%` energy,
    `62.79 K` wall RMSE, `62.69 K` centerline RMSE, and `26.69%` mass-flow
    error versus the current published frozen CFD contract.
  - The presentation-local tables intentionally stay on the currently published
    June 23 local stack instead of the still-running exact latest-window
    refresh, so the deck can be used immediately without mixing finished and
    in-flight evidence surfaces.
