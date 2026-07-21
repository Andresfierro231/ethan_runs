---
task: AGENT-349
date: 2026-07-14
role: Hydraulics / Implementer / Tester / Writer
status: complete
---
# Hydraulic Tap-Length Admission Refresh

Implemented the HYD-TAP slice from the hydraulic plan. The package consumes the
AGENT-338 hydraulic reset/K contract, July 8 two-tap minor-loss table, and
existing July 1 mesh-centerline station artifacts. It does not rerun OpenFOAM or
mutate solver outputs.

Outcome:

- `12` preserved corner rows now carry mesh-centerline endpoint chord lengths.
- `3` `test_section_complex` rows remain blocked because preserved evidence has
  no raw two-tap endpoint extraction.
- Recomputed component/cluster K diagnostics remain non-admitted: `6` rows are
  blocked by mesh/GCI after tap refresh, `6` remain recirculation diagnostics,
  and `3` remain missing centerline/raw two-tap evidence.
- H1 faithful rerun remains blocked; next hydraulic work is the external Fluid
  reset/development API and mesh/GCI-admitted pressure evidence.

No thermal fitting, native CFD mutation, external Fluid edit, scheduler action,
or global multiplier was used.
