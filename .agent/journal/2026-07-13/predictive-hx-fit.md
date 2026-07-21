# Predictive HX Fit

Date: `2026-07-13`  
Task: `TODO-PRED-HX-FIT`  
Role: Implementer / Tester / Writer

## Why This Avenue Exists

`TODO-PRED-FORWARD-V0` still consumes `imposed_cooler_duty_W`, so it is only
predictive conditional on cooler duty. The predictive-HX lane replaces that
runtime input with a low-dimensional fitted HX response while preserving
train/validation/holdout separation.

## Observed Facts

Created and validated:

- `tools/analyze/build_predictive_hx_fit.py`
- `tools/analyze/test_predictive_hx_fit.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/`

The generated package includes:

- `hx_model_forms.csv`
- `hx_validation_splits.csv`
- `hx_baseline_predictive_airside.csv`
- `hx_fit_parameters.csv`
- `hx_duty_scores.csv`
- `hx_primary_forward_scores.csv`
- `hx_litrev_gate_reference_audit.csv`
- `violations.csv`
- `summary.json`
- `README.md`

The implemented form is `HX1_global_qhx_multiplier_on_fluid_airside`, a single
global multiplier on Fluid's existing `predictive_airside_hx` duty. It is a
repo-local UA/effectiveness surrogate. The direct Fluid internal
`UA_multiplier` path is recorded as blocked because this task does not claim
external `../cfd-modeling-tools/**` edits.

## Split And Target Hygiene

Primary split:

- train: `salt_2`
- model-selection validation: `salt_3`
- holdout: `salt_4`

CFD/OpenFOAM cooler duty is used only as:

- training target evidence for `salt_2`, and
- validation/holdout scoring evidence for `salt_3` and `salt_4`.

It is not used as a runtime input in validation or holdout rows. The package
also carries the lit-rev gate audit from the predictive input contract.

## Results

Fitted multipliers:

- `F0_current_fluid_sources`: `2.53585363393`
- `F1_heater_only`: `2.80063797744`

`F1_heater_only` is the better thermal path in this provisional HX campaign:

- validation Salt 3: HX-duty error `-2.341 W`, Tmean error `6.534 K`.
- holdout Salt 4: HX-duty error `-17.511 W`, Tmean error `20.587 K`.

`F0_current_fluid_sources` remains poor thermally:

- validation Salt 3: HX-duty error `-12.916 W`, Tmean error `44.080 K`.
- holdout Salt 4: HX-duty error `-31.376 W`, Tmean error `56.895 K`.

Both variants still overpredict mdot relative to CFD; the held-out Salt 4 mdot
error is `0.009895 kg/s` for `F0` and `0.007395 kg/s` for `F1`.

## Inferred Interpretation

Replacing imposed cooler duty with a fitted HX surrogate is feasible in the
repo-local workflow. It improves the cooler-duty lane enough to keep the
predictive-HX path alive, especially under the heater-only source sensitivity.
It does not resolve the hydraulic problem or the heater/test-section source
contract. The HX fit must not be used to absorb those residuals.

## Validation

Commands:

- `module load python/3.12.11; python3 tools/analyze/test_predictive_hx_fit.py`
- `module load python/3.12.11; python3 tools/analyze/build_predictive_hx_fit.py --strict`
- `python -m json.tool work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/summary.json`

Results:

- 6 tests passed.
- Strict build passed with 0 violations.
- Summary JSON parsed.

## Remaining Blockers

- Direct UA multiplier inside Fluid requires a separate external source-edit
  task.
- Hydraulic overprediction remains a blocker before end-to-end claims.
- Heater/test-section transfer, wall/storage terms, sensor-map uncertainty, and
  thermal mesh/GCI remain open.
- The split has one train, one validation, and one holdout row; the result is a
  pathway/prototype, not a thesis-strength final calibration.

## Recommended Next Action

Use this campaign as input to `TODO-PRED-HYDRAULIC-GATE` and
`TODO-PRED-HEATER-TEST-CONTRACT`. Do not proceed to `TODO-PRED-ENDTOEND-SCORE`
until the hydraulic gate and heater/test contract are documented.

