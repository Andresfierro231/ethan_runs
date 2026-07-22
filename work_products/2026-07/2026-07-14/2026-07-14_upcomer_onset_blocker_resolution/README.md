---
provenance:
  - work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv
  - work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv
  - work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/upcomer_onset_regime_table.csv
  - reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/upcomer_recirculation_case_summary.csv
tags: [upcomer-onset, recirculation, blocker-resolution, thermal-closure]
related:
  - .agent/BLOCKERS.md
  - .agent/journal/2026-07-08/upcomer-onset.md
task: AGENT-324
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Onset Blocker Resolution

## Purpose

This package implements the upcomer-onset work packet from the project plan. It
consolidates the current onset evidence, documents the math and assumptions,
and states exactly what is still needed before a regime switch can be claimed.

## Result

The blocker remains open. Current admitted evidence has `3` points
from Re `71.1` to `134.9`. All `3`
points classify as `recirculation_cell_observed`; there are `0`
ordinary-pipe anchor points. Route A midpoint Re is `250.0`
and Route B midpoint Re is `167.5`, both above the current
maximum admitted Re if judged by midpoint.

## Files

- `upcomer_onset_evidence_status.csv`: current row-level evidence and allowed
  use.
- `math_and_theory.csv`: equations, assumptions, and implications.
- `next_evidence_requirements.csv`: minimum evidence needed to resolve the
  blocker.
- `blocker_status.csv`: one-row admission/blocker decision.
- `results_interpretation.md`: thesis-ready interpretation.
- `source_manifest.csv`: exact input provenance.

## Interpretation Boundary

Use this as blocker-resolution evidence and thesis wording. Do not use it as a
calibrated onset threshold, a single-stream upcomer friction closure, or an
internal-Nu admission.
