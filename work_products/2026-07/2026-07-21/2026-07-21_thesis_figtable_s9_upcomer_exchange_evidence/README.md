---
provenance:
  created_by: codex
  date: 2026-07-21
tags: [thesis, S9, upcomer, exchange, figure-table-package]
related:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
---

# S9 Upcomer Exchange Evidence Figure-Table Package

This package converts the completed S9 onset/exchange UQ study into thesis-ready table sources. It does not launch samplers, harvest data, edit rendered figures, or admit closures.

## Outputs

- `onset_regime_visual_table.csv`: recirculation/onset visual rows.
- `throughflow_exchange_schematic_table.csv`: schematic element states for throughflow, recirculation, exchange interface, residence time, and UQ.
- `exchange_qoi_figure_contract.csv`: figure contract for exchange QOIs.
- `missing_anchor_uq_table.csv`: missing-anchor and same-QOI UQ blockers.
- `caption_bank.md`, `source_manifest.csv`, `summary.json`, builder, checker, and README.

## Result

The visual package supports a thesis negative/diagnostic result: ordinary upcomer `Nu/f_D/K` remain disabled, exchange-cell coefficients remain unadmitted, and S11 remains blocked.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid/external source, generated indexes, thesis chapters, or figure assets were modified. No solver, sampler, harvest, fitting, tuning, model selection, ordinary upcomer admission, exchange-cell coefficient admission, S11 trigger, or final score claim was performed.
