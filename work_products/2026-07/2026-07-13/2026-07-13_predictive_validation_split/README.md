# Predictive Validation Split

Date: `2026-07-13`  
Task: `TODO-PRED-VALIDATION-SPLIT`  
Role: Coordinator / Writer

## Purpose

This package locks the train/validation/holdout admission rule before any
predictive thermal correction is fit. It does not change registry state, native
CFD outputs, or any fitting code.

## Open First

1. `admission_split_table.csv` for row-by-row assignment.
2. `response_variable_contract.csv` for fit versus score permissions.
3. `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md`
   for runtime-input guardrails.
4. `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md`
   for current forward-v0 scores.
5. `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/README.md`
   for wall-layer and radiation boundaries.

## Locked Current Split

| Row | Assignment | Fit Use | Score Use |
| --- | --- | --- | --- |
| `salt_2` | train | One predeclared family/global scalar thermal response at a time. Initial target is HX/cooler response. | Training residual only. |
| `salt_3` | validation | Not allowed. | Model-selection validation after the Salt2-trained scalar is frozen. |
| `salt_4` | holdout | Not allowed. | Final held-out endpoint after model form and validation decision are frozen. |
| `salt1_nominal` | diagnostic-only | Not allowed. | Context only until Salt1 policy and input-contract admission are explicit. |
| corrected-Q rows | blocked | Not allowed. | No scoring until row-specific admission; then validation/holdout first. |
| low-heat rows | blocked | Not allowed. | Archived diagnostics only until row-specific source and admission checks are redone. |

This is intentionally restrictive. With only three mainline Salt rows currently
in the predictive input contract, a two-or-more-parameter thermal correction is
not fit-admissible under this split.

## Fit Responses Versus Score Responses

Allowed fitting response for the current split is limited to one declared
physical thermal response, starting with the cooler/HX response. The fitted
quantity must be a global or family-level scalar and must be trained on
`salt_2` only.

Scoring responses may include CFD mdot, CFD Tmean, loop delta, Tmin/Tmax,
cooler duty, heat-ledger residuals, pressure residuals, and TP/TW sensors after
the sensor-map gate. These responses are joined after the solve; they are not
runtime inputs.

The following are not fit-admissible now:

- internal HTC/Nu/UA effective rows;
- passive external hA or wall-layer E1/E2 terms;
- test-section net heat terms before the heater/test-section contract;
- TP/TW sensor temperatures;
- pressure residuals or mdot as thermal tuning targets.

## Corrected-Q Entry Rule

Corrected-Q rows remain blocked today. Once a row-specific terminal/latest-time
gate admits a corrected-Q row, it enters as validation or holdout sensitivity
evidence, not as a new training row. Symmetric +/- pairs should be preferred:
if only one side of a pair is admitted, keep the row diagnostic-only unless a
new split revision explains why asymmetric scoring is scientifically safe.

Corrected-Q rows may support response-slope scoring after the mainline model
form and mainline scalar are frozen. They must not introduce per-case
parameters.

## Low-Heat Entry Rule

Low-heat rows remain blocked today. The June 23 freeze package recorded three
low-Q windows, but the current predictive heat-loss package explicitly did not
admit corrected-Q or low-heat rows, and later cleanup removed old invalid
perturbation roots. A low-heat row must therefore be requalified by exact source
path, terminal/latest-time evidence, thermal uncertainty, and predictive input
contract before scoring.

Once admitted, low-heat rows enter first as extrapolation validation/holdout
for a frozen mainline model. They do not train the initial HX or heater
correction.

## Per-Case Hack Block

No predictive thermal correction may use case-specific fitted values for
cooler duty, heater efficiency, test-section source, passive external hA,
wall-layer beta, internal Nu multiplier, or sensor offsets. Any future fit must
declare the family-level parameter count before fitting, preserve training,
validation, and holdout separation, and report residuals by hydraulic, cooler,
heater/test-section, passive external wall, and sensor lanes.

## Output Contract

- `admission_split_table.csv`: current row assignments and next gates.
- `response_variable_contract.csv`: fit/scoring permissions by response.
- `summary.json`: compact counts and decisions.

## Do Not Do

- Do not refit after looking at Salt3 validation or Salt4 holdout residuals.
- Do not promote corrected-Q or low-heat rows based on historical labels alone.
- Do not absorb pressure failures into thermal parameters.
- Do not separate radiation from CFD `wallHeatFlux` unless a later package
  provides a distinct `qr` term or controlled rerun.
