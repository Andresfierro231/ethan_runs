# AGENT-115 Raw Journal — Salt Heat-Loss Breakout

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-115`
- purpose:
  - replace the unreadable all-Salt heat-loss overlay with per-family figures
  - remove dashed and dotted role ambiguity
  - make the span chunks and TP endpoints explicit enough for presentation use
- files inspected:
  - `.agent/BOARD.md`
  - `reports/2026-06-15_ethan_field_transport_campaign/README.md`
  - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_package_index.csv`
  - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_streamwise_heat_comparison.csv`
  - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_grouped_heat_comparison.csv`
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/tp_tw_probe_locations.csv`
  - `tools/case_analysis_profiles.py`
  - representative `summary.json` and `leg_centerline_station_definitions.csv`
    files from the June 15 Salt-family case-analysis package roots
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-115.md`
  - `.agent/journal/2026-06-23/coordinator-implementer-writer-salt-heat-loss-breakout.md`
  - `imports/2026-06-23_ethan_salt_family_heat_loss_breakout.json`
  - `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
  - `reports/2026-06-23_ethan_salt_family_heat_loss_breakout/**`
- results or observations:
  - The original June 15 figure was hard to read because it combined all Salt
    cases and encoded role meaning by line style alone.
  - The new package uses one figure per Salt family and separates total,
    intended-transfer, and parasitic-loss components into different subplot
    rows.
  - The visible x ranges still reflect only the published streamwise heat rows,
    so the new figures explicitly describe gap regions as omitted corners,
    junctions, or unpublished bins rather than pretending the loop is fully
    continuous there.
  - `python3.11` lacked `matplotlib` in this environment; the working
    validation path used `python` (`3.9.7`) instead.
