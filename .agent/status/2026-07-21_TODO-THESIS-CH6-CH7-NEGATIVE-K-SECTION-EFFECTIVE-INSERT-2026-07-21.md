---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/README.md
tags: [thesis, negative-k, section-effective-pressure, closeout]
related:
  - .agent/journal/2026-07-21/thesis-ch6-ch7-negative-k-section-effective-insert.md
  - imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json
task: TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: status
status: complete
---
# TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21

## Objective

Insert the negative-K / section-effective residual result into the current
thesis dossier as a clean negative contribution: why current lower-right
component-K attempts stop, what the signed residual can still prove, and which
pressure/F6 claims remain forbidden.

## Outcome

Completed documentation-only insertions in Chapter 6, Chapter 7, and the
figure/table incorporation ledger. The thesis now states that the current
Salt2/Salt3/Salt4 lower-right pressure rows are not ordinary component-K rows,
but are retained as recirculating section-effective residual evidence
motivating `Delta_p_recirc_section`.

The chapter text carries the key evidence values: signed residuals of
`-1.25366731683 Pa`, `-1.84957005859 Pa`, and `-1.67833900273 Pa`, plus a
Salt2-frozen diagnostic transfer maximum error of
`0.47046606946166093438399 Pa` with `0/0/0` validation, holdout, and
external-test rows consumed.

## Changes Made

- `reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md`
- `reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md`
- `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/**`
- `.agent/status/2026-07-21_TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21.md`
- `.agent/journal/2026-07-21/thesis-ch6-ch7-negative-k-section-effective-insert.md`
- `imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json`

## Validation

- `python3.11 -m json.tool work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/summary.json` - pass.
- `python3.11 -m json.tool imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json` - pass.
- `git diff --check -- .agent/BOARD.md .agent/status/2026-07-21_TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21.md .agent/journal/2026-07-21/thesis-ch6-ch7-negative-k-section-effective-insert.md imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md` - pass.
- `python3 tools/docs/build_repo_index.py --check` - pass, blocker register OK with `15` entries.
- `python3.11 tools/agent/finish_task.py --task-id TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21` - pass.

## Unresolved Blockers

- Ordinary component-K/F6 admission remains blocked for current lower-right
  rows by reverse flow, missing same-basis straight/developing reference,
  missing component isolation, and missing same-QOI UQ.
- Numeric F3/Shah comparison remains blocked until an ordinary admissible F6
  row exists.
- Protected validation, holdout, and external-test scoring remain unused.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid
source, external repo files, validation/holdout/external scores, fitting,
tuning, model selection, closure admission, component-K/F6/cluster-K promotion,
clipped K, hidden/global multiplier, blocker register, generated index, or
runtime-leakage relaxation was changed.
