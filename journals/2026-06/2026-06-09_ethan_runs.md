# Ethan Runs Update

Date: 2026-06-09

## Observed Outputs

- Built `reports/2026-06-09_ethan_steady_state_heat_flow_audit/` with:
  - `README.md`
  - `summary.json`
  - `case_heat_inventory.csv`
  - `latest_heat_partition.csv`
  - `heat_window_summary.csv`
  - `tw_hypothesis_matrix.csv`
  - `rerun_recommendations.csv`
  - `figures/png|svg|pdf/cross_case_heat_partition_comparison.*`
  - `figures/png|svg|pdf/tw_rmse_vs_heat_partition_error.*`
- Added provenance for that analysis pass in `imports/2026-06-09_steady_state_heat_flow_audit.json`.
- The audit covered `13` registered CFD cases from `registry/case_registry.csv`; the separate `inventory_only` campaign row remained excluded.
- All `13` cases had a usable `50`-sample late wall-heat window under the current audit rule.
- The live `val_salt_test_2_coarse_mesh_laminar` continuation now shows wall-heat history through about `6830 s`, beyond the June 4 direct-validation snapshot at `3871 s`.

## Interpretation

- The cross-case steady-state heat partition is now clear enough to answer the immediate question "where is the heat going?" for every registered CFD case without launching new OpenFOAM postprocessing. The dominant explicit sink is always the cooling branch, and the junction bucket is the next recurring nontrivial sink after the cooler and test-section branch.
- The strongest family-level result is the salt-vs-water split in ambient-loss mismatch. Salt rows under-shoot the Ethan-linked ambient-loss reference by about `52.78 W` on average, while water rows under-shoot by only about `2.52 W`. That makes missing or mispartitioned wall loss the first TW suspect for the salt family.
- The new audit therefore supports the revised reduced-order-model direction: use the 3D cases to quantify where losses and source deposition actually sit, then feed those sectionwise values into the 1D ROM rather than forcing agreement through a 2D-bridge objective.
- Water cases look broadly self-consistent under the current heat-partition metrics: low TW RMSE and small ambient-loss error. The salt rows do not; their TW miss tracks with a persistent under-loss signal.

## Contradictions / Caveats

- This package reuses the June 4 direct-validation metrics for `exp_tw_rmse_k` and the Ethan-linked ambient-loss reference. For the live Salt 2 continuation that means the heat partition is newer than the TW scorecard.
- The report identifies a salt-family under-loss pattern, but it does not yet localize which missing loss path dominates physically: support conduction, junction-local exchange, heater-neighbor losses, or some combination.
- No DMDC or new 3D field postprocessing was touched in this pass. The scope stayed on existing `ethan_runs` postProcessing outputs and report infrastructure.

## Suggested Next Actions

- Refresh direct validation for `val_salt_test_2_coarse_mesh_laminar` against the current runtime snapshot if current TW values need to anchor decisions.
- Use `latest_heat_partition.csv` and `tw_hypothesis_matrix.csv` to design the next 1D-informed source/loss contract, especially for junction losses and nonuniform source placement.
- If we want a stronger physical attribution pass, add a follow-on report that decomposes the salt under-loss signal by base-case family and Jin/Kirst pair rather than only by whole-case totals.

## Checkpoint / Stopping Point

- The new stopping point for today is the completed `reports/2026-06-09_ethan_steady_state_heat_flow_audit/` package. It answers the cross-case steady-state heat-partition question well enough to stop without leaving an ambiguous half-built analysis path.
- The strongest actionable result is the salt-family under-loss signal: salt rows sit about `52.78 W` low on average versus the Ethan-linked ambient-loss reference, while water rows are only about `2.52 W` low.
- The next question is now narrower and better posed: which physical loss and source terms from the 3D cases should be transferred first into the 1D ROM?

## Tomorrow Todo

- Refresh the direct-validation package for the live Salt 2 continuation so `TW` metrics line up with the current `~6830 s` heat-tail horizon.
- Convert the salt under-loss result into a ranked shortlist of ROM-facing candidates: junction losses, test-section surroundings, support/parasitic losses, and source placement shape.
- Draft the first explicit 3D-to-1D source/loss contract proposal for the `Fluid` reduced-order model using the new `latest_heat_partition.csv` and `tw_hypothesis_matrix.csv` outputs.
