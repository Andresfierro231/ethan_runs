---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight/coarse_source_staging_repair_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/staging_repair_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/scheduler_submit_attempt.csv
tags: [s13, coarse, open-cv, extraction, staging-repair]
related:
  - .agent/status/2026-07-22_TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/README.md
task: TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer
type: journal
status: complete
---
# S13 Coarse Open-CV Extraction

Attempted: moved S13 past the direct-coarse staging blocker by implementing a
coarse extraction wrapper and running the minimal safe validation sequence.

Observed:

- The preflight repair contract had `12` missing target-minus destination
  files and `12` existing recorded source files.
- The repair copied Salt2 `7914`, Salt3 `7617`, and Salt4 `9999` fields for
  `T`, `rho`, `U`, and `wallHeatFlux`.
- After repair, all three current-coarse cases preflight as ready for
  compute-node sampling.
- A Salt2 one-window execute smoke completed and produced finite diagnostic
  rows for `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
  `tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K`.
- Full `sbatch` submission was not possible from this compute-node shell.

Inferred: S13 is no longer blocked by missing staged target-minus source files.
The next blocker is operational: submit the full direct-coarse extraction from
a login node, then consume those rows in residual and triplet gates. The science
guardrail remains unchanged: the smoke rows are diagnostic and cannot be used
for formal GCI, production harvest, coefficient admission, or final scoring.

Contradictions or caveats:

- The repaired staged fields are local copies, not native-output mutation.
- The Salt2 smoke used only one target-minus window; it proves extractor
  mechanics, not three-case/three-window completeness.
- `Q_wall_W` remains unreleased for thesis/admission use despite finite
  diagnostic values.

Next useful actions:

1. Submit
   `work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight/run_s13_coarse_open_cv_extraction.sbatch`
   from a login node.
2. When the full package has `3` geometry rows, `9` window reductions, and `36`
   direct coarse QOI rows, run the residual ledger builder.
3. Only after residual accounting exists, rerun the coarse-medium-fine triplet
   admission gate and formal GCI disposition.
