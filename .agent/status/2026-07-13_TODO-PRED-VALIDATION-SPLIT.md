# Status: TODO-PRED-VALIDATION-SPLIT

Date: 2026-07-13  
Role: Coordinator / Writer  
Owner: codex  
State: complete

## Scope

- `.agent/BOARD.md` own row only
- `.agent/status/2026-07-13_TODO-PRED-VALIDATION-SPLIT.md`
- `.agent/journal/2026-07-13/predictive-validation-split.md`
- `imports/2026-07-13_predictive_validation_split.json`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/**`

## Result

Defined the predictive validation split:

- `salt_2`: train for one predeclared global/family scalar thermal response.
- `salt_3`: validation.
- `salt_4`: holdout.
- `salt1_nominal`: diagnostic-only.
- corrected-Q and low-heat rows: blocked until row-specific admission.

## Blockers Preserved

- Corrected-Q rows require terminal/latest-time admission before scoring.
- Low-heat rows require source-path requalification and admission.
- Internal Nu/UA, passive external hA, E1/E2 wall-layer fitting, and sensor
  fitting remain blocked.

## Validation

- JSON manifest and summary parsed with `python3.11 -m json.tool`.
- Both CSV contracts parsed with Python `csv.DictReader`.
