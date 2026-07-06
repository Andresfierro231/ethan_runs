# AGENT-120 Raw Journal — Dynamic And Heat Figure Clarity

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-120`
- purpose:
  - resolve user confusion about why the June 23 dynamic-pressure package did
    not include `p_rgh(s)` on the same plot
  - explain the visible `q_dyn(s)` sawtooth with direct evidence from the
    published row table
  - rebuild the Salt-family heat-loss breakout with presentation-readable span
    labeling
- files inspected:
  - `.agent/BOARD.md`
  - `reports/2026-06-23_ethan_dynamic_pressure_profiles/README.md`
  - `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/README.md`
  - `reports/2026-06-23_ethan_salt_family_heat_loss_breakout/README.md`
  - `tools/analyze/build_ethan_dynamic_pressure_profiles.py`
  - `tools/analyze/build_ethan_prgh_vs_dynamic_profiles.py`
  - `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
  - `reports/2026-06-23_ethan_dynamic_pressure_profiles/dynamic_pressure_profile_rows.csv`
  - `reports/2026-06-23_ethan_salt_family_heat_loss_breakout/span_chunk_map.csv`
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-23_AGENT-120.md`
  - `.agent/journal/2026-06-23/coordinator-implementer-writer-dynamic-and-heat-figure-clarity.md`
  - `imports/2026-06-23_ethan_dynamic_and_heat_figure_clarity.json`
  - `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
  - `reports/2026-06-23_ethan_dynamic_pressure_profiles/README.md`
  - `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/README.md`
  - `reports/2026-06-23_ethan_salt_family_heat_loss_breakout/**`
- results or observations:
  - The user-facing confusion was real: the `q_dyn`-only package predates the
    later same-day `p_rgh(s)` versus `q_dyn(s)` overlay package, so the old
    README now points explicitly at the newer sibling package.
  - The `right_leg` Salt 2 Jin example shows the artifact directly: the first
    retained time alternates between `bulk_velocity_m_s ~= 0.01677` and
    `0.02122`, which yields `q_dyn ~= 0.2758` and `0.4418 Pa` over repeated
    bins. The spike train therefore comes from the preserved coarse-bin
    reduction, not from a smooth underlying oscillatory field.
  - The original heat-loss breakout was readable in content but not in
    typography because every subplot repeated all span and gap labels. The
    refresh moved those labels to one shared top strip, kept only light span
    shading in the data panels, and left the x-axis uncluttered enough for
    presentation use.
