---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - source-bounded-cv
  - journal
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
---

# S13 Source-Bounded CV Definition Journal

Task: `TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21`

Attempted: a first implementation streamed every mesh face and computed face
geometry before deciding whether the face bounded a selected CV. That run was
interrupted because it was unnecessarily slow. The builder was then patched to
classify face membership first and compute area/vector only for boundary or
interface faces; the optimized run completed and wrote the package.

Observed: the selected largest face-connected reverse-flow components contain
`71775`, `73349`, and `74256` cells for Salt2/Salt3/Salt4. The corresponding
exchange-interface ledgers contain `9796`, `10094`, and `10238` candidate
interface faces with finite outward normal conventions.

Observed: no case has trusted right-leg wall faces under the current source
boundary rule. Salt2/Salt3/Salt4 instead touch unreleased lower-leg patches:
`ncc_pipeleg_lower_09_fitting_end`, `pipeleg_lower_06_straight`,
`pipeleg_lower_07_bend`, `pipeleg_lower_08_straight`, and
`pipeleg_lower_09_fitting`.

Inferred: the prior reverse-flow masks identify a real recirculating region,
but not the S13 source-bounded upcomer exchange CV needed for wall/source and
sampler work. The selected components are lower-leg-connected and
wall-disconnected relative to the trusted right-leg wall patch list.

Caveat: finite interface faces and normals are useful diagnostic geometry, but
they are not enough to release a CV. Positive trusted wall area and removal or
classification of boundary escapes are mandatory before `Q_wall_W`, sampler
preflight rerun, harvest, UQ, or S11/S12/S13 candidate review.

Next useful actions: do not rerun S13 sampler preflight from this package. A
future row would need a different, defensible source-bounded geometry rule or a
revised trusted-wall/control-volume definition that produces positive trusted
wall faces and no untrusted boundary escapes across all three cases.
