# TODO-PRED-THERMAL-MESH-GATE Status

Role: Coordinator / Implementer / Tester / Writer
Date: `2026-07-13`
Status: `complete`

## Scope

Implement the post-AGENT-291 thermal mesh gate for Salt2-first UA/HTC/Nu work.
The task consumes existing medium and fine repaired thermal outputs only. It
does not run OpenFOAM, mutate native solver outputs, update registry/admission
state, or claim a closure-ready thermal result.

## Inputs Read

- Medium repaired thermal package:
  `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/`
- Fine repaired thermal package:
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/`
- Prior Closure-QOI mesh/GCI package:
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`
- Terminal Slurm evidence for AGENT-291 job `3293768`.

## Output Package

- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_qois.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_blockers.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_evidence.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/README.md`

## Result

The previous AGENT-284 thermal blocker, `blocked_missing_fine_thermal_extraction`,
is resolved by AGENT-291 terminal evidence and fine smoke output. The new gate
does not admit any thermal QOI to closure fitting:

- QOI rows: `7`
- Medium/fine two-level complete rows: `5`
- Fit-admissible rows: `0`
- Publication-ready thermal GCI rows: `0`
- Admission decisions: `blocked_sign_review=5`,
  `blocked_missing_two_level_value=1`, `blocked_downcomer_policy=1`

Key diagnostic rows:

- Lower-leg HTC: medium `457.342555912`, fine `460.760022775`,
  relative delta `0.747244449277%`, blocked by sign review and missing coarse
  thermal triplet.
- Lower-leg UA_prime: medium `40.0499199715`, fine `40.3559085303`,
  relative delta `0.764017903197%`, blocked by sign review and missing coarse
  thermal triplet.
- Lower-leg Nu: missing/nonfinite at both levels and direct Nu not admitted.
- Upcomer HTC: medium `77.9372395781`, fine `76.3976111781`,
  relative delta `-1.97547207001%`, blocked by sign review and missing coarse
  thermal triplet.
- Upcomer UA_prime: medium `6.69189468429`, fine `6.56088183088`,
  relative delta `-1.95778414917%`, blocked by sign review and missing coarse
  thermal triplet.
- Upcomer Nu: medium `4.28483646142`, fine `4.20884087818`,
  relative delta `-1.77359355316%`, blocked by sign review and missing coarse
  thermal triplet.
- Downcomer/right-leg thermal segment remains policy-blocked.

## Reusable Workflow

Added:

- `tools/analyze/build_thermal_mesh_gate.py`
- `tools/analyze/test_thermal_mesh_gate.py`

Default command:

```bash
python3.11 tools/analyze/build_thermal_mesh_gate.py \
  --scheduler-job-name s2_fine_T+ \
  --scheduler-state COMPLETED \
  --scheduler-exit-code 0:0 \
  --scheduler-elapsed 00:22:33 \
  --scheduler-node c318-016
```

The manual scheduler fields exist because direct shell `sacct` worked while a
nested Python `sacct` subprocess was sandbox-blocked. The summary records this
as `manual_sacct_observation`.

## Validation

- `python3.11 -m unittest tools.analyze.test_thermal_mesh_gate`
- `python3.11 -m py_compile tools/analyze/build_thermal_mesh_gate.py tools/analyze/test_thermal_mesh_gate.py`
- `python3.11 -m json.tool work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json`
- `wc -l` confirmed 7 data rows plus header in both QOI and blocker CSVs.

## Next Task

Open `thermal_admission_sign_heat_balance_review` before any new closure
claims. It should reconcile wallHeatFlux sign, enthalpy balance, segment heat
duty orientation, lower-leg Nu availability, downcomer policy, and coarse
thermal triplet availability.
