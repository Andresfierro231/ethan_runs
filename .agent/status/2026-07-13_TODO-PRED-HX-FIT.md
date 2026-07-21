# TODO-PRED-HX-FIT Status

Date: `2026-07-13`  
Role: Implementer / Tester / Writer  
Owner: codex  
Status: `COMPLETE`

## Scope

Completed the standalone predictive-HX fit campaign without editing Fluid
source, native CFD outputs, registry state, or other active campaign packages.

Assigned paths used:

- `.agent/BOARD.md` own row
- `.agent/status/2026-07-13_TODO-PRED-HX-FIT.md`
- `.agent/journal/2026-07-13/predictive-hx-fit.md`
- `imports/2026-07-13_predictive_hx_fit.json`
- `tools/analyze/build_predictive_hx_fit.py`
- `tools/analyze/test_predictive_hx_fit.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/**`

## Outcome

Generated:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/`

The campaign fits `HX1_global_qhx_multiplier_on_fluid_airside`, a one-parameter
multiplier on Fluid's existing `predictive_airside_hx` cooler duty. This is a
repo-local UA/effectiveness surrogate; the cleaner direct Fluid
`UA_multiplier` path is documented but blocked until an external Fluid edit row
claims that source.

Primary split:

- train: `salt_2`
- validation: `salt_3`
- holdout: `salt_4`

## Key Results

Primary fitted multipliers:

- `F0_current_fluid_sources`: `2.53585363393`
- `F1_heater_only`: `2.80063797744`

Primary held-out/scored results:

- `F0_current_fluid_sources` validation Salt 3: HX-duty error `-12.916 W`,
  Tmean error `44.080 K`, mdot error `0.008155 kg/s`.
- `F0_current_fluid_sources` holdout Salt 4: HX-duty error `-31.376 W`,
  Tmean error `56.895 K`, mdot error `0.009895 kg/s`.
- `F1_heater_only` validation Salt 3: HX-duty error `-2.341 W`,
  Tmean error `6.534 K`, mdot error `0.005655 kg/s`.
- `F1_heater_only` holdout Salt 4: HX-duty error `-17.511 W`,
  Tmean error `20.587 K`, mdot error `0.007395 kg/s`.

Interpretation: the heater-only source sensitivity remains the better thermal
lane after replacing imposed cooler duty with a train-fitted HX surrogate, but
hydraulic mdot remains high and should not be hidden in HX or thermal fitting.

## Validation

Commands run:

- `module load python/3.12.11; python3 tools/analyze/test_predictive_hx_fit.py`
- `module load python/3.12.11; python3 tools/analyze/build_predictive_hx_fit.py --strict`
- `python -m json.tool work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/summary.json`

Results:

- 6 focused tests passed.
- Strict package build passed with `n_violations=0`.
- Summary JSON parsed successfully.

## Provenance

Primary inputs:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/`
- `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Remaining Blockers

- Direct Fluid UA-multiplier implementation requires a separate external Fluid
  edit row.
- Heater/test-section transfer, wall/storage residuals, hydraulic gate, and
  thermal mesh uncertainty remain unresolved.
- The current fit has only one train row, one validation row, and one holdout
  row; treat it as a pathway result, not a final thesis-strength calibration.

