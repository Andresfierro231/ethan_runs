# Forward-v1 Hydraulic Unblock Plan Execution

Date: 2026-07-15
Task: AGENT-393

## Bottom Line

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.
The highest-priority unblock is now the PM5 matched pressure/upcomer field/parser
gap: replacement compute completed interactively, but parsed metrics are
incomplete and admitted rows are zero.

## Outputs

- `scheduler_snapshot.csv` (8 rows)
- `pm5_matched_pressure_upcomer_relaunch_decision.csv` (3 rows)
- `hydraulic_gate_refresh.csv` (5 rows)
- `forward_v1_post_overnight_gate_delta.csv` (5 rows)
- `sensor_map_policy_refresh.csv` (17 rows)
- `source_manifest.csv`
- `summary.json`

Scheduler note: direct shell `squeue`/`sacct` reads were used for the final
snapshot because the same calls from the Python subprocess were sandbox-limited.

## Recommended Next Run/Edit

Do not relaunch cancelled PM5 sbatch jobs `3295901`/`3295968` blindly. The
staged interactive replacement path completed, so the next edit is to repair the
matched-plane field extraction/parser contract for `U`, `rho`, `T`, wall
temperature, and `wallHeatFlux`, then rerun or reparse the staged PM5 helper.
After admitted PM5 pressure/upcomer metrics exist, refresh F6/onset and
internal-Nu gates.

## Guardrails

- No native CFD solver outputs were mutated.
- No external `../cfd-modeling-tools` files were edited.
- No scheduler jobs were launched by this package.
- AGENT-373 hydraulics jobs remain pending dependencies and were not duplicated.
- Sensor temperatures remain post-solve validation targets only.
