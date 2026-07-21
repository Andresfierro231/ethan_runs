# Predictive Validation Split

Date: 2026-07-13  
Role: Coordinator / Writer  
Task ID: `TODO-PRED-VALIDATION-SPLIT`  
Owner: codex

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/README.md`
- `.agent/status/README.md`
- `.agent/journal/README.md`
- `operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/**`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/**`
- `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/**`
- `work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/**`
- `work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/**`
- `imports/2026-06-23_ethan_cfd_freeze_checkpoint.json`
- selected corrected-Q and low-Q operational notes/journals from 2026-07-13

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_TODO-PRED-VALIDATION-SPLIT.md`
- `.agent/journal/2026-07-13/predictive-validation-split.md`
- `imports/2026-07-13_predictive_validation_split.json`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/response_variable_contract.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/summary.json`

## Observed Evidence

- Current predictive input contract contains mainline `salt_2`, `salt_3`, and
  `salt_4` rows.
- Forward-v0 emits scores for those three rows, with validation targets joined
  after solve.
- Predictive heat-loss path reports zero fit-candidate control-volume rows and
  says corrected-Q/low-heat rows are not admitted in that package.
- Corrected-Q latest-time table keeps all 14 corrected-Q registry rows at
  `closure_fit_admissible=no`.
- Salt1 terminal harvest is context-only and does not change closure-fit
  admission.
- Low-Q/low-heat rows have historical freeze-window evidence, but current
  packages do not admit them and old invalid perturbation roots were cleaned.

## Decisions

- Lock `salt_2` as the only current training row for a one-scalar thermal
  correction.
- Lock `salt_3` as validation and `salt_4` as final holdout.
- Keep Salt1 diagnostic-only until Salt1 policy and predictive input-contract
  admission are explicit.
- Keep corrected-Q and low-heat rows blocked today; once admitted, they enter
  as validation/holdout sensitivity or extrapolation evidence before any
  training use.
- Fit response is limited to one declared physical thermal response, initially
  cooler/HX. Tmean, loop delta, mdot, pressure, and sensors are scores, not
  thermal fitting targets.
- Per-case fitted thermal hacks are forbidden.

## Commands Run

- `pwd`
- `sed -n ...` on startup docs and relevant package READMEs
- `rg --files ...`
- `rg -n ...`
- `head ...` / `cat ...` on relevant CSV and JSON evidence
- `mkdir -p work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split`
- `python3.11 -m json.tool ...`
- `python3.11 -c "import csv; ..."`

## Results

The validation-split package is complete and parse-validated. No registry rows
or native CFD solver outputs were modified.

## Incomplete Lines

- A future row must rerun corrected-Q terminal/latest-time admission after the
  packed continuation finishes.
- Low-heat rows need exact source-path requalification before they can score
  the predictive model.
- Any two-or-more-parameter thermal model needs additional admitted rows or a
  new dated split before fitting.
