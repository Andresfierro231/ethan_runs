---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/staging_repair_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/s13_same_label_coarse_open_cv_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/dry_all_after_repair/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/scheduler_submit_attempt.csv
tags: [s13, coarse, open-cv, extraction, staging-repair, diagnostic]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/README.md
  - .agent/journal/2026-07-22/s13-coarse-open-cv-extraction-scheduler.md
  - imports/2026-07-22_s13_coarse_open_cv_extraction_scheduler.json
task: TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer/Reviewer
type: status
status: complete
---
# TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22

## Objective

Repair the staged current-coarse target-minus field gap, create the direct
current-coarse open-CV extractor wrapper, validate it with a bounded smoke, and
prepare full scheduler execution without admitting S13 evidence.

## Outcome

Decision: `s13_coarse_open_cv_extraction_smoke_ready_full_run_login_submit_needed_no_admission`.

- Staging repair: `12/12` missing target-minus files copied into the July
  staging tree from recorded `SOURCE_PROCESSORS64` paths.
- All-case dry preflight after repair: `3/3` coarse cases ready for
  compute-node sampling.
- Bounded execute smoke: Salt2 target-minus window `7914` completed with `1`
  geometry row, `1` window reduction, `4` finite diagnostic QOI rows, and `0`
  sampling errors.
- Full extraction: not submitted. Host `c318-008.ls6.tacc.utexas.edu` returned
  "sbatch not available on compute nodes. Use a login node."
- Admission status: still `0` formal GCI/admission/release/freeze/final-score
  claims.

## Changes Made

- Added `tools/extract/build_s13_coarse_open_cv_extraction.py`.
- Added `tools/extract/test_s13_coarse_open_cv_extraction.py`.
- Published `work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/`.
- Published `dry_all_after_repair/` under that package.
- Copied only the task-owned staged target-minus files listed in the repair
  contract.
- Recorded the failed compute-node `sbatch` attempt in
  `scheduler_submit_attempt.csv`.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_coarse_open_cv_extraction.py tools/extract/test_s13_coarse_open_cv_extraction.py`: passed.
- `python3.11 -m unittest tools.extract.test_s13_coarse_open_cv_extraction`: `4` tests passed.
- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --case-id salt_2 --max-windows 1`: dry preflight passed.
- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --repair-staging --max-cases 3 --max-windows 1`: copied `12` repair rows; post-repair preflight `3/3` ready.
- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --execute --case-id salt_2 --max-windows 1 --job-id smoke_salt2_one_window`: passed; emitted `4` diagnostic QOI rows and `0` sampling errors.
- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --output-root work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/dry_all_after_repair --max-cases 3`: passed; `3/3` rows ready.
- `sbatch work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight/run_s13_coarse_open_cv_extraction.sbatch`: not submitted from compute node; notice recorded.

## Remaining Blockers

- Full Salt2/Salt3/Salt4 three-window extraction must be submitted from a
  login node or approved login submission wrapper.
- Formal GCI still requires all direct coarse sampled rows, residual-complete
  open-CV ledger, and triplet admission gate.
- Same-QOI UQ/admission, source/property release, Qwall release, production
  harvest, and final scoring remain closed.

## Guardrails

No native solver output was mutated. Only task-owned staged target-minus field
copies were written. No registry mutation, Fluid/external edit, thesis edit,
source/property or Qwall release, production harvest, formal GCI/admission,
same-QOI UQ admission, validation/holdout/external-test scoring, freeze,
final-score claim, endpoint proxy substitution, hidden multiplier, or residual
absorption into internal Nu occurred.
