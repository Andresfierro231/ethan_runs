---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/case_qoi_strict_coarse_no_go.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/coarse_unlock_action_contract.csv
tags: [status, s13, recirculation, coarse-equivalence, mesh-gci, fail-closed]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/README.md
  - .agent/journal/2026-07-22/s13-strict-coarse-nogo-contract.md
  - imports/2026-07-22_s13_strict_coarse_nogo_contract.json
task: TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22

## Objective

Resolve strict same-label coarse disposition for S13 exchange-cell QOIs and
write a formal coarse no-go contract if current evidence cannot support formal
GCI/admission.

## Outcome

Decision: `s13_strict_same_label_coarse_no_go_formal_gci_blocked`.

Current coarse candidate rows exist for all `12` Salt2/Salt3/Salt4 case/QOI
combinations, but admitted same-label coarse rows remain `0`. The required
coarse-equivalence criteria pass rows remain `0/6`, so all `12` case/QOI rows
are formal no-go rows.

Formal GCI-ready rows: `0`.
Production harvest allowed rows: `0`.
Medium/fine exact-label rows remain complete diagnostic evidence: `72`.

## Changes Made

- Added builder:
  `tools/analyze/build_s13_strict_coarse_nogo_contract.py`.
- Added tests:
  `tools/analyze/test_s13_strict_coarse_nogo_contract.py`.
- Published work product:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/`.
- Published criteria audit, per-case/QOI no-go audit, per-QOI formal-GCI
  matrix, unlock action contract, source manifest, guardrails, summary, and
  README.
- Added the explicit replacement coarse dataset contract:
  `replacement_coarse_dataset_contract.csv`.

## Validation

- `python3.11 tools/analyze/build_s13_strict_coarse_nogo_contract.py`: passed.
- `python3.11 -m py_compile tools/analyze/build_s13_strict_coarse_nogo_contract.py tools/analyze/test_s13_strict_coarse_nogo_contract.py`: passed.
- `python3.11 -m unittest tools.analyze.test_s13_strict_coarse_nogo_contract`: `6` tests passed.
- Final rerun after replacement-contract hardening:
  `python3.11 -m unittest tools.analyze.test_s13_strict_coarse_nogo_contract`:
  `7` tests passed.

## Remaining Blockers

- Direct same-label coarse mesh evidence is not admitted for any S13 QOI/case.
- Geometry mask provenance, time-window equivalence, field/source/property
  basis, residual-complete CV basis, and same-QOI UQ/mesh disposition remain
  unresolved for coarse admission.
- `Q_wall_W` remains a useful low-spread diagnostic lane, but low medium/fine
  spread does not unlock formal GCI without admitted coarse evidence.
- Source-side heat-flow equivalence must remain a distinct QOI; it is not
  relabeled as wall `Q_wall_W`.

## Coordination Caveat

`task_context.py` reported a broad trigger-gated open S11 row that overlaps
`tools/analyze/` in pattern form. This S13 task stayed in newly named
S13-specific files and did not touch the S11 candidate/source-property lane.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, source/property or Qwall release, formal GCI run/admission, production
harvest, coefficient fitting/admission, validation/holdout/external-test
scoring, candidate freeze, final-score claim, S11/S12/S13/S15/S6 trigger,
endpoint proxy substitution, hidden multiplier, residual absorption into
internal Nu, blocker-register source change, generated-index refresh, deletion,
staging, commit, or runtime-leakage relaxation occurred.
