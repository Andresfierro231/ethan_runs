# Ethan Salt Pressure-Drop Predictivity

Generated: `2026-06-29T16:55:15-05:00`

## Scope

- Salt-only additive package covering all 9 June 22 frozen-state references.
- Publishes a defended 3D pressure-budget summary built from the preserved case-analysis products.
- Publishes a local hydraulic replay table that holds the CFD pressure-drive fixed and asks how much mdot error remains under several reduced pressure-drop contracts.

## Output tables

- `cfd_pressure_budget_elements.csv`: one ordered hydraulic element table per frozen Salt reference.
- `cfd_pressure_budget_summary.csv`: one frozen-reference contract row with major/feature totals and reduced hydraulic resistances.
- `cfd_sensor_reference.csv`: CFD TP/TW references for downstream 1D-vs-CFD scoring.
- `local_hydraulic_replay.csv`: local mdot replay rows for the five named attempts.
- `local_hydraulic_replay_summary.csv`: attempt-level mdot replay summary.

## Notes

- Best hydraulic-only local replay by mean |mdot| error: `major_plus_feature_probe_baseline`.
- Attempts 4 and 5 intentionally share the same local hydraulic replay as attempt 3; their thermal distinctions only appear in the true 1D study lane.
- Case count: `9`.
