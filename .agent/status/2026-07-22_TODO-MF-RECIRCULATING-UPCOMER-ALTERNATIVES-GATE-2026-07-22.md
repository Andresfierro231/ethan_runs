---
provenance:
  generated_by: tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py
  task_id: TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22
  generated_at_utc: 2026-07-22T14:17:27.579688+00:00
task: TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22
tags: [status, recirculating-upcomer, alternatives-gate]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_recirc_upcomer_alternatives_gate
---
# TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22

## Objective

Compare recirculating-upcomer alternatives after S13 target-plus/temporal-UQ,
mesh/GCI, onset, MF09, and MF10 evidence, while keeping ordinary upcomer
closures disabled unless every source/UQ gate passes.

## Outcome

Decision: `diagnostic_only_no_admission`. Alternatives reviewed:
`4`. Candidate-reviewable alternatives:
`0`. Production-harvest prerequisites
passed: `1`.

Throughflow-plus-recirculation remains the preferred science lane, but it is
blocked by same-label mesh/GCI, source-property/cp, production harvest, and
onset-anchor gaps. Ordinary upcomer `Nu/f_D/K` remains disabled.

## Changes Made

- Wrote alternatives matrix.
- Wrote onset/data-sparsity gate.
- Wrote production-harvest prerequisite table.
- Wrote no-admission/S11 gate, source manifest, README, summary, journal, and
  import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py tools/analyze/test_mf_recirc_upcomer_alternatives_gate.py` passed.
- `python3.11 -m unittest tools.analyze.test_mf_recirc_upcomer_alternatives_gate` passed.

## Guardrails

- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler/solver/sampler/UQ launch: false.
- Validation/holdout/external scoring: false.
- Fitting/tuning/model selection: false.
- Source/property or Qwall release: false.
- Ordinary upcomer closure admission and exchange-cell coefficient admission:
  false.
- S11/S12/S13/S15/S6 trigger: false.
- Residual absorbed into internal Nu: false.
