---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/corrected_q_harvest_3295437_processing_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/recommended_salt_split.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
tags: [cfd-pp, corrected-q, admission, split-discipline, journal]
related:
  - .agent/status/2026-07-14_AGENT-353.md
  - imports/2026-07-14_corrected_q_pm5_admission_split_processing.json
task: AGENT-353
date: 2026-07-14
role: cfd-pp/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Corrected-Q +/-5Q Admission/Split Processing

Implemented the completed-harvest slice of the forward-v1 plan.

Observed facts:

- Corrected-Q harvest job `3295437` completed and exposed four read-only
  registry aggregate rows: `salt2_lo5q`, `salt2_hi5q`, `salt4_lo5q`, and
  `salt4_hi5q`.
- All four are terminal-gate closure-fit admissible in the AGENT-347 status
  table.
- The current split policy still allows `0` independent training expansion rows.

Interpretation:

- Salt2 +/-5Q is train-family perturbation evidence, but not independent
  training data.
- Salt4 +/-5Q is holdout-family perturbation evidence and must not be used for
  model selection.
- Final-window heat-role reductions are now available as diagnostic score
  targets for setup-only boundary/HX work, not as predictive runtime inputs.

Validation:

```text
python3.11 -m unittest tools.analyze.test_corrected_q_pm5_admission_split_processing
...
Ran 3 tests in 0.114s
OK
```

No native solver outputs, registry files, generated indexes, scheduler state, or
external Fluid files were modified.
