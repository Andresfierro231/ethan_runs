# AGENT-117 Raw Journal — Presentation Refresh And Figure Pack

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-117`
- purpose:
  - refresh the June 23 presentation package so the deck matches the completed
    same-day analysis packages
  - stage a local figure pack so slide assembly does not depend on scattered
    package-relative paths
  - make the remaining external replay boundary explicit instead of leaving it
    mixed with local deck work
- files inspected:
  - `.agent/BOARD.md`
  - `reports/2026-06-23_presentation/README.md`
  - `reports/2026-06-23_presentation/slide_outline.md`
  - `reports/2026-06-23_presentation/presentation_takeaways.md`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/README.md`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/surface_summary.csv`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/scenario_shadow_summary.csv`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface/figures/png/primary_scenario_metric_heatmap.png`
  - `reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface/figures/png/primary_branch_development.png`
  - `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/README.md`
  - `reports/2026-06-23_ethan_salt_redevelopment_followon/README.md`
  - `.agent/status/2026-06-23_AGENT-111.md`
  - `.agent/status/2026-06-23_AGENT-112.md`
  - `.agent/status/2026-06-23_AGENT-113.md`
  - `.agent/status/2026-06-23_AGENT-116.md`
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-117.md`
  - `.agent/journal/2026-06-23/coordinator-implementer-writer-presentation-refresh-and-figure-pack.md`
  - `imports/2026-06-23_presentation.json`
  - `tools/analyze/build_ethan_presentation_refresh.py`
  - `reports/2026-06-23_presentation/README.md`
  - `reports/2026-06-23_presentation/slide_outline.md`
  - `reports/2026-06-23_presentation/presentation_takeaways.md`
  - `reports/2026-06-23_presentation/figures/**`
- results or observations:
  - The presentation package now has a local staged figure pack with `10` main
    slides and `3` backups, each with PNG/PDF copies and explicit provenance in
    `reports/2026-06-23_presentation/figures/figure_manifest.csv`.
  - The new local Slide 10 summary figure is generated from the current bakeoff
    CSVs rather than from ambiguous older top-level bakeoff figures, so the deck
    now says exactly what is locally done versus what remains externally stale.
  - The current bounded 1D message did not improve: the defended full-coverage
    readable winner is still the baseline `1.0 in`, radiation-on scenario, and
    it still carries roughly `11.27%` heater-duty mismatch plus `~63 K`
    temperature RMSE scales.
  - The remaining live deck boundary is the external `Fluid` replay refresh on
    `AGENT-102`; the deck no longer has a missing local slide-asset blocker.
