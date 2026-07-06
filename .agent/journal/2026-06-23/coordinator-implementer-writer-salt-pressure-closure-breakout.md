# AGENT-118 Raw Journal — Salt Pressure-Closure Breakout

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-118`
- purpose:
  - replace the unreadable all-Salt straight-section pressure-closure scatter
    with per-family figures
  - make the span-by-span hydraulic comparison presentation-legible
  - surface TP endpoint labels directly on the figure instead of forcing the
    reader to infer loop position from the old package
- files inspected:
  - `.agent/BOARD.md`
  - `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/README.md`
  - `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/package_index.csv`
  - `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/pressure_closure_by_section.csv`
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/tp_tw_probe_locations.csv`
  - representative `summary.json` and `leg_centerline_station_definitions.csv`
    files from the June 15 retained Salt analysis package roots
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-118.md`
  - `.agent/journal/2026-06-23/coordinator-implementer-writer-salt-pressure-closure-breakout.md`
  - `imports/2026-06-23_ethan_salt_pressure_closure_breakout.json`
  - `tools/analyze/build_ethan_salt_pressure_closure_breakout.py`
  - `reports/2026-06-23_ethan_salt_pressure_closure_breakout/**`
- results or observations:
  - The original June 17 figure was hard to read because it overlaid all Salt
    cases and all straight sections in one scatter, so family differences and
    spatial labels were both competing for the same canvas.
  - The new package uses one figure per Salt family and three stacked panels:
    hydro-corrected loss, endpoint `p_rgh` loss, and the residual between
    them.
  - Endpoint `p_rgh` loss was chosen over integrated `p_rgh` loss because it
    exists on all five straight Salt spans, whereas the integrated quantity is
    only populated on `lower_leg` and `right_leg` in the June 17 table.
  - `python3.11` lacked `matplotlib` in this environment; the working
    validation path used `python` (`3.9.7`) instead.
