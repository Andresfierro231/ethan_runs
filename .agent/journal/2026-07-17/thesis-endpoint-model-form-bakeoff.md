---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/README.md
tags: [journal, thesis, model-form-bakeoff, final-split]
related:
  - .agent/status/2026-07-17_TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF.md
  - imports/2026-07-17_thesis_endpoint_model_form_bakeoff.json
task: TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF
date: 2026-07-17
role: Writer/Reviewer/Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester
type: journal
status: complete
---
# Thesis Endpoint Model-Form Bakeoff

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `reports/AGENTS.override.md`
- `reports/thesis_dossier/README.md`
- `reports/thesis_dossier/Outline.md`
- `reports/thesis_dossier/Chapters_and_sections/current/README.md`
- `reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md`
- `reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md`
- `reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md`
- `reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md`
- AGENT-499 corrected split package
- AGENT-500 val_salt2 external score/unlock package
- AGENT-503 val_salt2 pressure/corner-K diagnosis package
- AGENT-507 wall/passive/test-section admission closeout package
- AGENT-509 final predictive scorecard shell package
- AGENT-454 predictive boundary submodel admission package
- AGENT-461 coupled M3+TS test-section scorecard package

## Files Changed

- Added `tools/analyze/build_thesis_endpoint_model_form_bakeoff.py`
- Added `tools/analyze/test_thesis_endpoint_model_form_bakeoff.py`
- Generated `work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/**`
- Updated `reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md`
- Added `.agent/status/2026-07-17_TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF.md`
- Added this journal entry
- Added `imports/2026-07-17_thesis_endpoint_model_form_bakeoff.json`
- Updated `.agent/BOARD.md` own TODO row

## Observations

The locked split is clear and was preserved: Salt1-4 nominal are training rows;
Salt2 +/-5Q and `val_salt2` are score-only; PM10/future +/-10Q and new CFD are
future-gated. AGENT-499 and AGENT-509 both show that a final Salt1-4 nominal
frozen prediction artifact is still missing.

M1 and M3 have useful legacy numeric score context from the earlier Salt2/Salt3
/Salt4 method-development split. Those numbers were retained as diagnostic or
legacy context only, not final locked-split performance.

M2 has admitted heater/cooler boundary residual evidence from AGENT-454, with
the largest held-out boundary residual in this table being `7.50262 W` for the
cooler/HX term. The full predictive model is still blocked by wall/test-section
physics per AGENT-507.

M4 has junction-aware attribution evidence, but AGENT-503 reports `0`
fit-admitted corner-K entries and AGENT-500 reports `0` junction coefficient
admissions. M4 is therefore a thesis-useful attribution form, not an admitted
predictive coefficient form.

## Commands Run

- `python3 -m py_compile tools/analyze/build_thesis_endpoint_model_form_bakeoff.py tools/analyze/test_thesis_endpoint_model_form_bakeoff.py`
- `python3 -m unittest tools.analyze.test_thesis_endpoint_model_form_bakeoff`
- `python3 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/summary.json`

## Results

The generated package contains:

- `model_form_contracts.csv`
- `model_form_scores.csv`
- `model_form_costs.csv`
- `model_form_failure_modes.csv`
- `thesis_claim_ledger.csv`
- `runtime_leakage_audit.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`

Validation passed with 7 tests. Runtime audit failures: `0`.

## Caveats

This package does not compute a true final predictive score because no admitted
Salt1-4 nominal freeze exists. Numeric M1/M3 entries are explicitly legacy or
diagnostic. M2 is partial boundary evidence. M4 is diagnostic attribution
evidence until junction/corner admission gates pass.

## Next Steps

Use this package as the thesis source for M0-M4. Future work should add M5/M6
only after upcomer/onset and final-freeze blockers are resolved, and should keep
the same locked split.
