---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_direct_recirc_model_forms_and_dry_scorers/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_direct_recirc_model_forms_and_dry_scorers/summary.json
tags: [status, direct-recirculation, dry-scorer]
related:
  - .agent/journal/2026-07-20/direct-recirc-model-forms-and-dry-scorers.md
  - imports/2026-07-20_direct_recirc_model_forms_and_dry_scorers.json
task: TODO-DIRECT-RECIRC-MODEL-FORMS-AND-DRY-SCORERS
date: 2026-07-20
role: Coordinator/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-DIRECT-RECIRC-MODEL-FORMS-AND-DRY-SCORERS Status

## Result

- Froze `UH1`, `CR1`, and `ROX1` as direct recirculation research forms.
- Implemented dry scorecards for UH1 upcomer severity and CR1 corner residual diagnostics.
- Added a regime gate table and next-step path for all four research avenues.

## Validation

- `python3 -m unittest tools.analyze.test_direct_recirc_model_forms_and_dry_scorers`
- `python3 tools/analyze/build_direct_recirc_model_forms_and_dry_scorers.py`
