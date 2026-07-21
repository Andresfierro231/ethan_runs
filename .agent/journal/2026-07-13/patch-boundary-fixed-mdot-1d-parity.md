# Patch-Boundary Fixed-mdot 1D Parity

- date: 2026-07-13
- task ID: AGENT-271
- role: Coordinator / Implementer / Tester / Writer
- owner: codex
- branch/worktree: ethan_runs working tree

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py`
- `tools/analyze/build_thermal_boundary_patch_role_table.py`
- `tools/analyze/build_thermal_mismatch_remedy_deep_dive.py`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit/radiation_parity_decision.json`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/AGENTS.override.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_AGENT-271.md`
- `.agent/journal/2026-07-13/patch-boundary-fixed-mdot-1d-parity.md`
- `imports/2026-07-13_patch_boundary_fixed_mdot_1d_parity.json`
- `tools/analyze/run_patch_boundary_fixed_mdot_1d_parity.py`
- `tools/analyze/test_patch_boundary_fixed_mdot_1d_parity.py`
- `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/**`

## Commands Run

- `python tools/analyze/run_patch_boundary_fixed_mdot_1d_parity.py --plan-only --strict`
- `pytest -q tools/analyze/test_patch_boundary_fixed_mdot_1d_parity.py`
- `python tools/analyze/run_patch_boundary_fixed_mdot_1d_parity.py --strict`

## Observed Outputs

- Contract rows: 15
- Section heat-balance rows: 24
- Run-plan rows: 15
- Fixed-mdot result rows: 12
- Path-summary rows: 4
- Validation errors: 0
- Focused tests: 5 passed

`path_summary.csv` reports:

- `B0_current_fluid_baseline`: mean absolute Tmean error `63.745917 K`
- `B1_legacy_cfd_cooler_duty`: mean absolute Tmean error `4.456196 K`
- `B2_realized_wallflux_roles`: mean absolute Tmean error `157.560104 K`
- `B3_imposed_setup_roles`: mean absolute Tmean error `177.254638 K`

## Interpretation

The cooler-role duty replay remains the best fixed-mdot thermal diagnostic.
The full fixed-Q realized and imposed ledgers are useful for heat-balance and
sign-convention diagnosis, but they are poor absolute-temperature anchors in
the current Fluid API because they remove the temperature-dependent external
boundary network. This is consistent with the package decision to keep
`B4_external_bc_equivalent_contract` as contract-only until a Fluid-owned task
can represent h/Ta/Tsur/emissivity/layers directly.

AGENT-264 is enforced as `inseparable`: realized CFD `wallHeatFlux` already
contains the boundary-condition radiation effect where `rcExternalTemperature`
is active, so no separate 1D radiation correction was added.

## Contradictions Or Caveats

- AGENT-267 was already active for an unrelated reconstructed-`T` task, so this
  implementation used AGENT-271 instead of the originally planned number.
- `B1_legacy_cfd_cooler_duty` must use cooler-role heat only, not the whole
  cooling-branch segment loss; the script now does that.
- `B2` and `B3` are diagnostic fixed-Q modes, not a full external-boundary
  parity model.

## Next Steps

- Use `section_heat_balance.csv` and `fixed_mdot_parity_results.csv` for an
  AGENT-272 residual diagnosis: identify which sections require a
  temperature-dependent boundary model rather than fixed-Q replay.
- Open a separate Fluid-owned task if true external-boundary parity is needed:
  add per-segment or per-patch h/Ta/Tsur/emissivity/layer inputs with combined
  convection/radiation and no double-counted `wallHeatFlux` radiation.
