# Thermal Interface Power Policy

Date: `2026-07-08`
Role: Coordinator / Writer
Task ID: `AGENT-213`
Branch/worktree: current `ethan_runs` workspace

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/DECISIONS.md`
- `.agent/README.md`
- `.agent/status/README.md`
- `.agent/journal/README.md`
- `work_products/2026-07-08_thermal_boundary_contract/README.md`
- `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/README.md`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_replay_results.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/remedy_path_summary.csv`

## Files Changed

- `.agent/BOARD.md`
- `.agent/DECISIONS.md`
- `.agent/status/2026-07-08_AGENT-213.md`
- `.agent/journal/2026-07-08/thermal-interface-power-policy.md`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`

## Observed Facts

- Heater imposed duty is larger than heater heat into the CFD fluid:
  - Salt 2: 265.700 W imposed, 243.519 W heater `wallHeatFlux` into fluid.
  - Salt 3: 297.500 W imposed, 273.155 W heater `wallHeatFlux` into fluid.
  - Salt 4: 337.600 W imposed, 310.487 W heater `wallHeatFlux` into fluid.
- Current 1D cooler removal in the fixed-mdot replay is much smaller than the
  CFD cooler removal:
  - Salt 2: 46.292 W current 1D cooler, 136.351 W CFD cooler removal.
  - Salt 3: 49.663 W current 1D cooler, 150.770 W CFD cooler removal.
  - Salt 4: 53.472 W current 1D cooler, 169.227 W CFD cooler removal.
- The July 8 thermal boundary contract marks Salt CFD rows as having
  surface-emissivity metadata but no separate `qr` radiation output term.

## Inferred Interpretation

For CFD-informed comparison, the correct 1D thermal interface contract is the
heat that crosses the CFD fluid boundary, not idealized equipment power. The
resistor wattage and cooler hardware model are future predictive inputs; they
should not be treated as realized fluid heat transfer until the corresponding
submodels pass validation.

## Commands Run

```bash
pwd
sed -n '1,220p' AGENTS.md
sed -n '1,260p' .agent/BOARD.md
sed -n '1,220p' .agent/FILE_OWNERSHIP.md
sed -n '1,220p' .agent/ROLES.md
rg --files -g 'AGENTS.override.md'
sed -n '1,260p' .agent/DECISIONS.md
sed -n '1,220p' work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv
sed -n '1,220p' work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_replay_results.csv
sed -n '1,220p' work_products/2026-07-08_thermal_boundary_contract/README.md
```

Validation commands run after edits:

```bash
rg -n "AGENT-213|TODO-PREDICT-HEATER|TODO-PREDICT-COOLER|TODO-1D-RADIATION" .agent/BOARD.md
rg -n "wallHeatFlux|cooler_removed_duty_W|CFD-informed|radiation" operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md .agent/DECISIONS.md
```

Result: both searches returned the expected board rows and policy terms.

## Incomplete Lines of Investigation

- Predicting the fraction of resistor dissipated power that reaches the fluid is
  now boarded as `TODO-PREDICT-HEATER-FLUID-FRACTION`.
- Predicting actual cooler heat removal from hardware/geometry inputs is now
  boarded as `TODO-PREDICT-COOLER-REMOVAL`.
- Adding or verifying 1D radiation heat-loss capability is now boarded as
  `TODO-1D-RADIATION-CAPABILITY`.

## Next Step

Future thermal replays should cite
`operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md` and
state whether they are CFD-informed or fully predictive.
