---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
tags: [status, external-bc, source-sink, provenance]
related:
  - .agent/journal/2026-07-21/extbc-source-sink-provenance-recovery.md
  - imports/2026-07-21_extbc_source_sink_provenance_recovery.json
task: TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Writer / Reviewer
type: status
status: complete
---
# TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21

## Objective

Recover setup-side heater/cooler/test-section source/sink provenance and decide
whether any rows can move beyond realized-CFD-only provenance.

## Outcome

Complete. The package reviewed `12` source/sink rows and recovered `12`
setup-known candidate rows from staged `0/T` setup files. Runtime-admitted
source/sink rows remain `0` pending a source-model API and source/property gate.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21.md`
- `.agent/journal/2026-07-21/extbc-source-sink-provenance-recovery.md`
- `imports/2026-07-21_extbc_source_sink_provenance_recovery.json`
- `work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/**`

## Validation

- `python3.11 -m json.tool .../summary.json`: passed.
- Package CSV row/column validation: passed.
- `python3.11 tools/docs/build_repo_index.py --check` passed: `blocker register OK (15 entries)`.

## Unresolved Blockers

Source/sink setup provenance is recovered, but runtime use remains blocked by
missing source-model API release and candidate-specific source/property split
release.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest launch, Fluid/external edit,
validation/holdout/external-test scoring, fit/model selection, source/property
release, freeze/admission, blocker-register change, generated-index refresh, or
thesis edit.
