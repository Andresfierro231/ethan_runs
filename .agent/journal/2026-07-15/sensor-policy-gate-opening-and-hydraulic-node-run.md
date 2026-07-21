# Sensor Policy, Gate Opening, And Hydraulic Node Run

2026-07-15T08:21:37-0500 - Claimed AGENT-405 to answer gate-opening questions, create a standalone sensor-map policy artifact, and run safe AGENT-373 diagnostics on the current compute node without mutating AGENT-373 outputs.

2026-07-15T08:23:00-0500 - Built and tested `tools/analyze/build_sensor_policy_gate_opening_and_hydraulic_node_run.py`. The package separates target-only sensor policy, internal-Nu reopening criteria, closure-QOI mesh/GCI criteria, PM5 run decision, and hydraulic node-run status.

2026-07-15T08:24:00-0500 - Ran the three safe AGENT-373 stages on `c318-008` under allocation `3295120` into `work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/`: raw two-tap preflight, F6 gate refresh, and Fluid reset-K diagnostic sweep.

2026-07-15T08:25:00-0500 - Read-only Slurm check confirmed the original AGENT-373 submitted jobs `3295989`, `3295990`, and `3295991` remain pending. They were not cancelled because cancellation was not explicitly requested.

2026-07-15T08:25:40-0500 - Closed AGENT-405. Internal-Nu and closure-QOI mesh/GCI remain closed; sensor-map policy is open as a post-solve target-only contract; PM5 needs targeted resampling rather than blind relaunch; local hydraulic diagnostics completed on this node.

2026-07-15T08:28:23-0500 - Added explicit hydraulic admission and residual-attribution outputs after the user asked whether raw two-tap/F6/reset-K landed and were admitted. Result: reset-K/localized-K component separation is diagnostic-admitted only; raw two-tap and F6 are not admitted; PM5 remains partial; final hydraulic residual attribution is provisional and cannot be called final until scratch-safe raw pressure extraction and full PM5/F6 evidence land.
