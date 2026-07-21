# AGENT-208 Journal: Thermal Boundary Contract and Frozen Replay Plan

Date: `2026-07-08`
Role: Coordinator / Implementer / Writer

## Work Completed

Created `tools/analyze/build_thermal_boundary_contract.py` and
`tools/analyze/test_thermal_boundary_contract.py`.

Generated `work_products/2026-07-08_thermal_boundary_contract/` with:

- `cfd_thermal_boundary_contract.csv`
- `span_heat_residuals.csv`
- `case_thermal_targets.csv`
- `fluid_solver_state_audit.csv`
- `frozen_hydraulics_replay_plan.csv`
- `test_plan.csv`
- `summary.json`
- `README.md`

Wrote the operational note:

- `operational_notes/07-26/08/2026-07-08_thermal_boundary_contract_and_frozen_replay_plan.md`

## Observed Facts

- The generated contract has 24 patchwise rows: 12 ambient-wall rows and three
  each for heater, cooler, test-section, and junction-other.
- The preserved CFD Salt contract label is
  `cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`.
- The prior 1D row `predictive_airside_ins_1.0in_rad_1` is hotter than CFD by
  61.950 K, 63.698 K, and 66.201 K for Salt 2/3/4.
- The same prior 1D row has loop delta T smaller than CFD by 3.908 K, 3.907 K,
  and 3.722 K for Salt 2/3/4.
- Heater imposed duty exceeds realized heater wallHeatFlux by 22.181 W,
  24.345 W, and 27.113 W.
- No heat-ledger `qr` radiation term is present; emissivity metadata is not the
  same as a resolved radiation heat term.
- The current Fluid solver has 3D source/loss hooks, but no explicit
  fixed-mdot/frozen-hydraulics scenario field was found.

## Interpretation

The current Salt mismatch is a thermal boundary/state reconstruction problem
before it is a friction-closure problem.  The next credible 1D sequence is a
frozen-hydraulics replay with CFD mdot held near target, patchwise heat terms
preserved with sign conventions, and only documented thermal boundary terms
iterated until mean T and loop delta T match CFD.

The model-form bakeoff should stay blocked until the generated replay gate is
met: `abs(Tmean error) <= 2 K` and `abs(loop delta T error) <= 1 K` for all
admitted Salt cases.

## Validation

Commands run:

```bash
python3.11 tools/analyze/build_thermal_boundary_contract.py
python3.11 -m unittest tools.analyze.test_thermal_boundary_contract
python3.11 -m py_compile tools/analyze/build_thermal_boundary_contract.py tools/analyze/test_thermal_boundary_contract.py
```

Results:

- Builder completed.
- 5/5 focused tests passed.
- Syntax check passed.

## Next Recommended Action

Implement or review a Fluid fixed-mdot/frozen-hydraulics thermal replay hook or
wrapper.  Without that, replay stages that claim to isolate thermal boundary
effects from hydraulic/friction behavior are not yet paper-grade.
