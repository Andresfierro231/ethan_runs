---
provenance:
  - tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/s12_unlock_gate.csv
tags: [s13, upcomer, exchange-cell, source-bounded-cv, s12, journal]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition.json
task: TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Upcomer Exchange Source-Bounded CV Definition

## Attempted

Built a task-owned source-bounded CV package to decide whether existing S13
evidence was sufficient to unlock sampler refresh and S12-HIAX1. The builder
joined the completed topology CV release, alternate-CV topology forensics,
sampler-manifest preflight, interface/wall/source recovery, and geometry
contract into one release table and one S12 unlock gate.

## Observed

- The three Salt train cases all remain `blocked_source_bounded_cv_not_released`.
- Largest reverse-flow topology components expose diagnostic internal interface
  faces, but have `0` trusted right-leg wall faces.
- Alternate wall-contact components are absent for Salt2 and tiny for
  Salt3/Salt4, with `6` and `15` right-leg wall faces respectively.
- Source and thermal lanes remain blocked because no released CV defines wall,
  core, normal, and exchange-state conventions.
- `s12_unlock_gate.csv` keeps S12-HIAX1 blocked and explicitly forbids
  implementation without released exchange-state QOIs.

## Inferred

S13 is not blocked by file plumbing at this stage. It is blocked by the absence
of a physically source-bounded exchange CV. The velocity-only reverse-flow mask
is useful diagnostic evidence, but it is not a sufficient runtime input for S12
or same-QOI UQ.

## Contradictions and Caveats

- Diagnostic interface faces exist for all three cases, so the failure is not a
  total topology parse failure.
- The existence of small Salt3/Salt4 wall-contact fragments does not release
  the group because the all-three-case and source-bounded gates fail.
- No thresholds were relaxed and no proxy faceZone was promoted to an exchange
  interface.

## Next Useful Actions

1. Audit whether the dominant reverse-flow ROI and trusted right-leg wall patch
   set describe the same region.
2. If misaligned, define a predeclared geometry-backed right-leg/upcomer seed
   tied to trusted wall patches before applying velocity diagnostics.
3. Rerun source-bounded CV release after the geometry seed exists.
4. Keep sampler refresh, harvest, same-QOI UQ, S12 implementation, freeze,
   validation, holdout, external-test, and S11/S15/S6 triggers blocked until
   the source-bounded CV releases.
